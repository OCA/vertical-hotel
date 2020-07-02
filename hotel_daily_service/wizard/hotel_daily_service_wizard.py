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
    hotel_service_line_ids = fields.Many2many(
        comodel_name="hotel.service.line",
        string="Service Lines",
        relation="hotel_service_line_daily_service_wizard",
    )
    quantity = fields.Integer(string="Quantity", default=1)

    @api.model
    def default_get(self, field_names):
        defaults = super().default_get(field_names)
        defaults["hotel_folio_id"] = self.env.context["active_id"]
        return defaults

    @api.onchange("quantity")
    def onchange_quantity(self):
        for line in self.hotel_service_line_ids:
            line.product_uom_qty = self.quantity

    @api.onchange("hotel_service_id")
    def onchange_hotel_service_id(self):
        self.hotel_service_line_ids = [(5, 0, 0)]
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
            service_line = self.env["hotel.service.line"].create(
                {
                    "order_id": self.hotel_folio_id.order_id.id,
                    "ser_checkin_date": date,
                    "ser_checkout_date": date,
                    "product_id": self.hotel_service_id.product_id.id,
                    "product_uom_qty": self.quantity,
                    "product_uom": self.hotel_service_id.product_id.uom_id.id,
                    "price_unit": self.hotel_service_id.product_id.list_price,
                }
            )
            self.hotel_service_line_ids |= service_line

    @api.multi
    def add_daily_service_line(self):
        self.ensure_one()
        self.hotel_folio_id.service_lines |= self.hotel_service_line_ids
