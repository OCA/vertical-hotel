from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HotelDailyServiceLineWizard(models.TransientModel):
    _name = "hotel.daily.service.line.wizard"
    _description = "Hotel Daily Service Line"

    @api.model
    def _default_hotel_service_id(self):
        rec = self.env["hotel.services"].search([], limit=1)
        if not rec:
            raise ValidationError(_("Please define a service first."))
        return rec

    hotel_folio_id = fields.Many2one(
        comodel_name="hotel.folio", string="Folio"
    )
    hotel_service_id = fields.Many2one(
        comodel_name="hotel.services",
        string="Service",
        default=_default_hotel_service_id,
    )
    quantity = fields.Integer(
        string="Quantity",
        default=1,
        help="Quantity of the services to be added each day.",
    )
    include_checkin_day = fields.Boolean(
        string="Include Arrival Day", default=False
    )
    note = fields.Text(string="Note")

    @api.model
    def default_get(self, field_names):
        defaults = super().default_get(field_names)
        defaults["hotel_folio_id"] = self.env.context["active_id"]
        return defaults

    @api.multi
    def add_daily_service_line(self):
        self.ensure_one()
        checkin_date = fields.Datetime.from_string(
            self.hotel_folio_id.checkin_date
        )
        checkout_date = fields.Datetime.from_string(
            self.hotel_folio_id.checkout_date
        )
        for date in [
            checkin_date + timedelta(days=n)
            for n in range(int((checkout_date - checkin_date).days) + 1)
        ]:
            if self.include_checkin_day or date != checkin_date:
                service_line = self.env["hotel.service.line"].create(
                    {
                        "order_id": self.hotel_folio_id.order_id.id,
                        "ser_checkin_date": date,
                        "ser_checkout_date": date,
                        "product_id": self.hotel_service_id.product_id.id,
                        "product_uom_qty": self.quantity,
                        "product_uom": self.hotel_service_id.product_id.uom_id.id,
                        "price_unit": self.hotel_service_id.product_id.list_price,
                        "note": self.note,
                    }
                )
                self.hotel_folio_id.service_lines |= service_line
