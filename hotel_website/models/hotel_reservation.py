# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command


class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    is_website_booking = fields.Boolean(
        "Booked Online",
        readonly=True,
        copy=False,
        help="Requested on the website. The guest chose room types; rooms of "
        "those types are assigned when the reservation is confirmed.",
    )

    def _awaiting_room_assignment(self):
        """Website requests whose lines still carry only a room type."""
        return self.filtered(
            lambda res: (
                res.is_website_booking
                and res.state == "draft"
                and any(not line.reserve for line in res.reservation_line)
            )
        )

    @api.constrains("reservation_line", "adults", "children")
    def _check_reservation_rooms(self):
        # A website request legitimately has no rooms until the front desk
        # confirms it; everything else keeps hotel_reservation's check.
        awaiting = self._awaiting_room_assignment()
        res = super(HotelReservation, self - awaiting)._check_reservation_rooms()
        for reservation in awaiting:
            if any(
                not line.categ_id and not line.reserve
                for line in reservation.reservation_line
            ):
                raise ValidationError(
                    self.env._("Each reservation line needs a room type or a room.")
                )
        return res

    def confirmed_reservation(self):
        self._assign_website_rooms()
        return super().confirmed_reservation()

    def _assign_website_rooms(self):
        """Give each room-type-only line of a website request a free room of
        that type, cheapest first, before the usual confirmation runs."""
        room_obj = self.env["hotel.room"]
        for reservation in self.filtered("is_website_booking"):
            empty_lines = reservation.reservation_line.filtered(
                lambda line: not line.reserve
            )
            if not empty_lines:
                continue
            taken = reservation.reservation_line.reserve
            for line in empty_lines:
                free = (
                    room_obj._hotel_website_free_rooms(
                        line.categ_id,
                        reservation.checkin,
                        reservation.checkout,
                        reservation.company_id,
                    )
                    - taken
                )
                if not free:
                    raise UserError(
                        self.env._(
                            "No %(room_type)s room is free for this stay any more. "
                            "Select a room on the line manually or change the dates.",
                            room_type=line.categ_id.name,
                        )
                    )
                reservation.write(
                    {
                        "reservation_line": [
                            Command.update(
                                line.id, {"reserve": [Command.set(free[:1].ids)]}
                            )
                        ]
                    }
                )
                taken |= free[:1]
            # Rooms are known now: run hotel_reservation's full check,
            # capacity included.
            reservation._check_reservation_rooms()
