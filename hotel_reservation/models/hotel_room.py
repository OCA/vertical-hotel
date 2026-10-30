# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date

# Longest period shown by the reservation summary, in days.
SUMMARY_MAX_DAYS = 92


class HotelRoom(models.Model):
    _inherit = "hotel.room"
    _description = "Hotel Room"

    room_reservation_line_ids = fields.One2many(
        "hotel.room.reservation.line", "room_id", string="Room Reserve Line"
    )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_confirmed_reservation(self):
        for room in self:
            if any(line.status == "confirm" for line in room.room_reservation_line_ids):
                raise ValidationError(
                    self.env._("Cannot delete room with confirmed reservations.")
                )

    @api.model
    def _get_booked_rooms(
        self,
        checkin,
        checkout,
        exclude_reservations=None,
        include_folios=True,
        reservation_states=None,
    ):
        """Rooms with a stay overlapping [checkin, checkout).

        A stay blocks a room when it starts before the other one ends: a
        stay ending when the next one starts does not (same rule as
        hotel.folio's double-booking check). Stays are the room bookings of
        reservations that are not cancelled and, with ``include_folios``,
        the room lines of folios that are not cancelled."""
        booking_domain = [
            ("check_in", "<", checkout),
            ("check_out", ">", checkin),
            ("status", "not in", ("cancel", "draft")),
        ]
        if reservation_states:
            booking_domain.append(("status", "in", tuple(reservation_states)))
        if exclude_reservations:
            booking_domain.append(
                ("reservation_id", "not in", exclude_reservations.ids)
            )
        rooms = (
            self.env["hotel.room.reservation.line"]
            .sudo()
            .search(booking_domain)
            .room_id
        )
        if include_folios:
            rooms |= (
                self.env["folio.room.line"]
                .sudo()
                .search(
                    [
                        ("check_in", "<", checkout),
                        ("check_out", ">", checkin),
                        ("folio_id.state", "!=", "cancel"),
                    ]
                )
                .room_id
            )
        return rooms.with_env(self.env)

    def _update_room_status(self):
        """Occupied while a stay is in progress, available otherwise.

        Only the rooms whose status changes are written."""
        now = fields.Datetime.now()
        in_house = self._get_booked_rooms(now, now + timedelta(seconds=1))
        to_occupy = self.filtered(lambda r: r in in_house and r.status != "occupied")
        to_free = self.filtered(lambda r: r not in in_house and r.status != "available")
        if to_occupy:
            to_occupy.write({"isroom": False})
        if to_free:
            to_free.write({"isroom": True})

    @api.model
    def cron_room_line(self):
        """
        This method is for scheduler
        every 1min scheduler will call this method and check Status of
        room is occupied or available
        --------------------------------------------------------------
        @param self: The object pointer
        @return: update status of hotel room reservation line
        """
        # every room: the status of each one depends on the current time
        self.search([])._update_room_status()  # pylint: disable=no-search-all
        return True


class RoomReservationSummary(models.Model):
    _name = "room.reservation.summary"
    _description = "Room reservation summary"

    name = fields.Char("Reservation Summary", default="Reservations Summary")
    date_from = fields.Date(default=fields.Date.context_today)
    date_to = fields.Date(
        default=lambda self: fields.Date.context_today(self) + relativedelta(days=30),
    )
    summary_data = fields.Json(compute="_compute_summary_data")

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for summary in self:
            if (
                summary.date_from
                and summary.date_to
                and summary.date_from > summary.date_to
            ):
                raise ValidationError(
                    self.env._("Checkout date should be later than Checkin date.")
                )

    def room_reservation(self):
        """
        @param self: object pointer
        """
        resource_id = self.env.ref("hotel_reservation.view_hotel_reservation_form").id
        return {
            "name": self.env._("Room Reservation"),
            "context": dict(self.env.context),
            "view_mode": "form",
            "res_model": "hotel.reservation",
            "views": [(resource_id, "form")],
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.depends("date_from", "date_to")
    def _compute_summary_data(self):
        for summary in self:
            summary.summary_data = summary._get_summary_data()

    def get_room_summary(self):
        """Kept for callers of the 19.0 API: the summary is a computed field."""
        return self._get_summary_data()

    def _get_summary_data(self):
        """Rooms × days grid of the period, in the user's timezone.

        ``{"days": [{"date", "label"}], "rooms": [{"id", "name", "cells":
        [{"date", "state", "res_model", "res_id", "label"}]}]}`` where state
        is ``free``, ``reserved`` (confirmed reservation) or ``folio``."""
        empty = {"days": [], "rooms": []}
        if not (self.date_from and self.date_to) or self.date_from > self.date_to:
            return empty
        date_to = min(self.date_to, self.date_from + timedelta(days=SUMMARY_MAX_DAYS))
        days = [
            self.date_from + timedelta(days=i)
            for i in range((date_to - self.date_from).days + 1)
        ]
        tz = ZoneInfo(self.env.context.get("tz") or self.env.user.tz or "UTC")

        def to_utc(day):
            local = datetime.combine(day, time.min, tzinfo=tz)
            return local.astimezone(UTC).replace(tzinfo=None)

        def to_local_date(value):
            return value.replace(tzinfo=UTC).astimezone(tz).date()

        start, end = to_utc(days[0]), to_utc(days[-1] + timedelta(days=1))
        # pylint: disable=no-search-all
        rooms = self.env["hotel.room"].search([], order="name, id")
        stays = {}  # (room id, day) -> cell

        def mark(room, check_in, check_out, cell):
            first, last = to_local_date(check_in), to_local_date(check_out)
            # nights: the departure day is free again, a same-day stay takes one day
            day, stop = first, max(last, first + timedelta(days=1))
            while day < stop:
                stays[(room.id, day)] = cell
                day += timedelta(days=1)

        bookings = self.env["hotel.room.reservation.line"].search(
            [
                ("room_id", "in", rooms.ids),
                ("check_in", "<", end),
                ("check_out", ">", start),
                ("reservation_id.state", "=", "confirm"),
            ]
        )
        for booking in bookings:
            mark(
                booking.room_id,
                booking.check_in,
                booking.check_out,
                {
                    "state": "reserved",
                    "res_model": "hotel.reservation",
                    "res_id": booking.reservation_id.id,
                    "label": booking.reservation_id.reservation_no or "",
                },
            )
        # folios last: a reservation turned into a folio shows the folio
        folio_lines = self.env["folio.room.line"].search(
            [
                ("room_id", "in", rooms.ids),
                ("check_in", "<", end),
                ("check_out", ">", start),
                ("folio_id.state", "!=", "cancel"),
            ]
        )
        for line in folio_lines:
            mark(
                line.room_id,
                line.check_in,
                line.check_out,
                {
                    "state": "folio",
                    "res_model": "hotel.folio",
                    "res_id": line.folio_id.id,
                    "label": line.folio_id.display_name or "",
                },
            )
        free = {"state": "free", "res_model": False, "res_id": False, "label": ""}
        return {
            "days": [
                {
                    "date": fields.Date.to_string(day),
                    "label": format_date(self.env, day, date_format="EEE d MMM"),
                }
                for day in days
            ],
            "rooms": [
                {
                    "id": room.id,
                    "name": room.name or "",
                    "cells": [
                        dict(
                            stays.get((room.id, day), free),
                            date=fields.Date.to_string(day),
                        )
                        for day in days
                    ],
                }
                for room in rooms
            ],
        }
