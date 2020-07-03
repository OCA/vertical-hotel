# See LICENSE file for full copyright and licensing details.

from odoo import api, models


class HotelFolio(models.Model):
    _inherit = "hotel.folio"

    @api.multi
    def write(self, vals):
        res = super(HotelFolio, self).write(vals)
        for rec in self:
            if (
                bool(vals.get("duration"))
                or bool(vals.get("adults"))
                or bool(vals.get("children"))
            ) and not bool(
                vals.get("service_lines")  # prevent recursion
            ):
                rec.update_tourist_tax()
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.update_tourist_tax()
        return res

    @api.multi
    def update_tourist_tax(self):
        self.ensure_one()

        # Remove existing taxes
        for service_line in self.service_lines:
            if service_line.product_id in self.env["hotel.tourist.tax"].search(
                []
            ).mapped("hotel_service_id.product_id"):
                self.service_lines = [(2, service_line.id, 0)]

        # Add taxes
        for tax in self.env["hotel.tourist.tax"].search(
            [("auto_apply", "=", True)]
        ):
            total = (
                tax.amount
                * (self.duration if tax.per_night else 1)
                * (
                    (self.adults if tax.count_adults else 0)
                    + (self.children if tax.count_children else 0)
                    if tax.per_person
                    else 1
                )
            )

            service_line = self.env["hotel.service.line"].create(
                {
                    "order_id": self.order_id.id,
                    "ser_checkin_date": self.checkin_date,
                    "ser_checkout_date": self.checkout_date,
                    "product_id": tax.hotel_service_id.product_id.id,
                    "product_uom_qty": 1,
                    "product_uom": tax.hotel_service_id.product_id.uom_id.id,
                    "price_unit": total,
                }
            )
            self.service_lines |= service_line
