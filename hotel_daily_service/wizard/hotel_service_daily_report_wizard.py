from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Date


class HotelDailyServiceLineWizard(models.TransientModel):
    _name = "hotel.service.daily.report.wizard"
    _description = "Hotel Daily Service Line"

    @api.model
    def _default_hotel_service_id(self):
        rec = self.env["hotel.services"].search([], limit=1)
        if not rec:
            raise ValidationError(_("Please define a service first."))
        return rec

    hotel_service_id = fields.Many2one(
        comodel_name="hotel.services",
        string="Service",
        default=_default_hotel_service_id,
    )
    date = fields.Date(string="Date", default=fields.Date.today)
    only_daily = fields.Boolean(
        string="Only Daily Services",
        default=True,
        help="Only include services where "
        "the service's From Date and To Date are the same.",
    )

    @api.multi
    def action_hotel_service_daily_report(self):
        service_lines = self.env["hotel.service.line"].search([])
        service_lines = service_lines.filtered(
            lambda sl: fields.Date.from_string(sl.ser_checkin_date)
            == Date.from_string(self.date)
        )
        service_lines = service_lines.filtered(
            lambda sl: sl.service_line_id.product_id
            == self.hotel_service_id.product_id
        )
        service_lines = service_lines.filtered(
            lambda sl: sl.folio_id.state not in ["cancel"]
        )
        if self.only_daily:
            service_lines = service_lines.filtered(
                lambda sl: sl.ser_checkin_date == sl.ser_checkout_date
            )
        if not service_lines:
            raise ValidationError(
                _("No service lines comply with these filters")
            )
        return self.env.ref(
            "hotel_daily_service.hotel_service_daily_report_action"
        ).report_action(service_lines)
