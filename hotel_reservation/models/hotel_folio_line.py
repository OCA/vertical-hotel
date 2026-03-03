# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class HotelFolioLine(models.Model):
    _inherit = "hotel.folio.line"

    @api.onchange("checkin_date", "checkout_date")
    def _onchange_checkin_checkout_dates(self):
        res = super()._onchange_checkin_checkout_dates()
        avail_prod_ids = []
        for room in self.env["hotel.room"].search([]):
            assigned = False
            for line in room.room_reservation_line_ids.filtered(
                lambda l: l.status != "cancel"
            ):
                if self.checkin_date and line.check_in and self.checkout_date:
                    if (self.checkin_date <= line.check_in <= self.checkout_date) or (
                        self.checkin_date <= line.check_out <= self.checkout_date
                    ):
                        assigned = True
                    elif (line.check_in <= self.checkin_date <= line.check_out) or (
                        line.check_in <= self.checkout_date <= line.check_out
                    ):
                        assigned = True
            if not assigned:
                avail_prod_ids.append(room.product_id.id)
        return res

    def write(self, vals):
        ReservationLine = self.env["hotel.room.reservation.line"]
        Room = self.env["hotel.room"]
        prod_id = vals.get("product_id") or self.product_id.id
        checkin = vals.get("checkin_date") or self.checkin_date
        checkout = vals.get("checkout_date") or self.checkout_date
        is_reserved = self.is_reserved
        if prod_id and is_reserved:
            prod_room = Room.search([("product_id", "=", prod_id)], limit=1)
            if self.product_id and self.checkin_date and self.checkout_date:
                old_prod_room = Room.search(
                    [("product_id", "=", self.product_id.id)], limit=1
                )
                if prod_room and old_prod_room:
                    rm_lines = ReservationLine.search(
                        [
                            ("room_id", "=", old_prod_room.id),
                            ("check_in", "=", self.checkin_date),
                            ("check_out", "=", self.checkout_date),
                        ]
                    )
                    if rm_lines:
                        rm_line_vals = {
                            "room_id": prod_room.id,
                            "check_in": checkin,
                            "check_out": checkout,
                        }
                        rm_lines.write(rm_line_vals)
        return super().write(vals)
