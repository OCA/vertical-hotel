# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class HotelFolioLine(models.Model):
    _inherit = "hotel.folio.line"

    def write(self, vals):
        """
        Overrides ORM write method to update Hotel Room Reservation line history.
        @param vals: dictionary of field values.
        """
        if {"product_id", "checkin_date", "checkout_date"} & set(vals):
            reservation_line_obj = self.env["hotel.room.reservation.line"]
            room_obj = self.env["hotel.room"]
            for line in self.filtered(
                lambda line: (
                    line.is_reserved
                    and line.product_id
                    and line.checkin_date
                    and line.checkout_date
                )
            ):
                old_room = room_obj.search(
                    [("product_id", "=", line.product_id.id)], limit=1
                )
                new_room = room_obj.search(
                    [("product_id", "=", vals.get("product_id", line.product_id.id))],
                    limit=1,
                )
                if old_room and new_room:
                    reservation_line_obj.search(
                        [
                            ("room_id", "=", old_room.id),
                            ("check_in", "=", line.checkin_date),
                            ("check_out", "=", line.checkout_date),
                        ]
                    ).write(
                        {
                            "room_id": new_room.id,
                            "check_in": vals.get("checkin_date", line.checkin_date),
                            "check_out": vals.get("checkout_date", line.checkout_date),
                        }
                    )
        return super().write(vals)
