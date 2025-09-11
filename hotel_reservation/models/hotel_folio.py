# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HotelFolio(models.Model):
    _inherit = "hotel.folio"
    _order = "reservation_id desc"

    reservation_id = fields.Many2one(
        "hotel.reservation", "Reservation", ondelete="restrict"
    )

    def write(self, vals):
        res = super().write(vals)
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        for folio in self:
            reservations = reservation_line_obj.search(
                [("reservation_id", "=", folio.reservation_id.id)]
            )
            if len(reservations) == 1:
                update_vals = []
                for line in folio.reservation_id.reservation_line:
                    for room in line.reserve:
                        update_vals.append(
                            {
                                "room_id": room.id,
                                "check_in": folio.checkin_date,
                                "check_out": folio.checkout_date,
                                "state": "assigned",
                                "reservation_id": folio.reservation_id.id,
                            }
                        )
                if update_vals:
                    reservations.write(update_vals[0])
        return res
