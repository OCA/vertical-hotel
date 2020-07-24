# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import date, timedelta

from odoo import api, models
from odoo.fields import Date, Datetime


class HotelRoom(models.Model):
    _inherit = "hotel.room"

    @api.multi
    def get_room_status(self, day):
        """day: date object"""
        assert type(day) == date, "day arg should be of type datetime.date"
        self.ensure_one()

        #  Rooms could be booked in a folio that is made without coming
        #   from a reservation (or some folio dates could be changed etc). We
        #   chose to not use the `hotel.room.reservation.line` entries for
        #   this module, but to lower the risk of errors we could either:
        #  * Also check the folio's and see if the room is in one of them
        #  * Force folio's to come from a reservation
        reservation_lines = self.env["hotel_reservation.line"].search(
            [
                ("line_id.state", "in", ["draft", "confirm", "done"]),
                ("reserve", "=", self.id),
                # checkin during the day or sooner
                ("checkin", "<=", Date.to_string(day)),
                # checkout during the day or later
                ("checkout", ">=", Date.to_string(day)),
            ]
        )
        draft_lines = reservation_lines.filtered(
            lambda rl: rl.line_id.state == "draft"
        )

        if len(reservation_lines) == 0:
            return "free", reservation_lines
        elif len(reservation_lines) == len(draft_lines):
            return "draft", reservation_lines
        else:
            return "busy", reservation_lines

    @api.multi
    def get_room_daily_summary(self, day):
        """day: date object"""
        assert type(day) == date, "day arg should be of type datetime.date"
        self.ensure_one()

        room_status, reservation_lines = self.get_room_status(day)
        room_status_text = reservation_lines.get_room_summary_cell_text(day)

        daily_summary = {
            "date": Datetime.to_string(day),
            "state": room_status,
            "state_text": room_status_text,
            "room_id": self.id,
        }
        return daily_summary

    @api.multi
    def get_room_summary(self, date_from, date_to):
        """
        :param date_from: datetime.datew
        :param date_to: datetime.date
        :return:
        """
        self.ensure_one()
        nb_days = (date_to - date_from).days

        days = (date_from + timedelta(days=i) for i in range(nb_days))

        room_summary = {
            "name": self.name,
            "room_id": self.id,
            "value": [self.get_room_daily_summary(day) for day in days],
        }
        return room_summary
