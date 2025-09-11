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
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        room_obj = self.env["hotel.room"]

        if self.is_reserved and (
            "product_id" in vals or "checkin_date" in vals or "checkout_date" in vals
        ):
            prod_id = vals.get("product_id", self.product_id.id)
            checkin = vals.get("checkin_date", self.checkin_date)
            checkout = vals.get("checkout_date", self.checkout_date)

            if self.product_id and self.checkin_date and self.checkout_date:
                old_prod_room = room_obj.search(
                    [("product_id", "=", self.product_id.id)], limit=1
                )
                new_prod_room = (
                    room_obj.search([("product_id", "=", prod_id)], limit=1)
                    if prod_id != self.product_id.id
                    else old_prod_room
                )

                if old_prod_room and new_prod_room:
                    reservation_line_obj.search(
                        [
                            ("room_id", "=", old_prod_room.id),
                            ("check_in", "=", self.checkin_date),
                            ("check_out", "=", self.checkout_date),
                        ]
                    ).write(
                        {
                            "room_id": new_prod_room.id,
                            "check_in": checkin,
                            "check_out": checkout,
                        }
                    )

        return super().write(vals)
