# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HotelFolio(models.Model):
    _inherit = "hotel.folio"
    _order = "reservation_id desc"

    reservation_id = fields.Many2one(
        comodel_name="hotel.reservation",
        ondelete="restrict",
    )

    def write(self, vals):
        res = super().write(vals)
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        for folio in self:
            reservations = reservation_line_obj.search(
                [("reservation_id", "=", folio.reservation_id.id)]
            )
            if len(reservations) != 1:
                continue
            for room in folio.reservation_id.reservation_line.reserve:
                values = {
                    "room_id": room.id,
                    "check_in": folio.checkin_date,
                    "check_out": folio.checkout_date,
                    "state": "assigned",
                    "reservation_id": folio.reservation_id.id,
                }
                reservations.write(values)
        return res
