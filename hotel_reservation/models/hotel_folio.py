# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HotelFolio(models.Model):
    _inherit = "hotel.folio"
    _order = "reservation_id desc"

    reservation_id = fields.Many2one(
        "hotel.reservation", ondelete="restrict", index=True
    )

    def write(self, vals):
        res = super().write(vals)
        if "checkin_date" in vals or "checkout_date" in vals:
            # keep the room bookings of the reservation on the stay dates
            for folio in self.filtered("reservation_id"):
                self.env["hotel.room.reservation.line"].search(
                    [("reservation_id", "=", folio.reservation_id.id)]
                ).write(
                    {
                        "check_in": folio.checkin_date,
                        "check_out": folio.checkout_date,
                    }
                )
        return res
