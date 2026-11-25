# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command

# Days a website request waits for the front desk before it is cancelled,
# when the setting is not set.
DEFAULT_REQUEST_EXPIRY_DAYS = 3


class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    is_website_booking = fields.Boolean(
        "Booked Online",
        readonly=True,
        copy=False,
        help="Requested on the website. The guest chose room types; rooms of "
        "those types are assigned when the reservation is confirmed.",
    )
    website_request_ip = fields.Char(
        "Request IP Address",
        readonly=True,
        copy=False,
        groups="base.group_system",
        help="Address the website request was sent from; limits how many "
        "requests one visitor can send.",
    )

    @api.model
    def _hotel_request_expiry_days(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_int("hotel_website.request_expiry_days", DEFAULT_REQUEST_EXPIRY_DAYS)
        )

    @api.model
    def _cron_expire_website_requests(self):
        """Cancel the website requests nobody confirmed in time.

        A request holds no room: past the delay, or once its arrival date
        has passed, it is cancelled and the guest is told, so it does not
        wait in the list forever."""
        days = self._hotel_request_expiry_days()
        now = fields.Datetime.now()
        domain = [("is_website_booking", "=", True), ("state", "=", "draft")]
        expired = self.search(domain + [("checkin", "<", now)])
        if days > 0:
            expired |= self.search(
                domain + [("create_date", "<", now - timedelta(days=days))]
            )
        for reservation in expired:
            reservation.cancel_reservation()
            if reservation.partner_id.email:
                reservation.message_post(
                    body=self.env._(
                        "We could not confirm your reservation request %(number)s "
                        "in time, so it has been cancelled and no room is held "
                        "for you. Please contact us or send a new request.",
                        number=reservation.reservation_no,
                    ),
                    partner_ids=reservation.partner_id.ids,
                    author_id=reservation.company_id.partner_id.id,
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                )
        return expired

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
