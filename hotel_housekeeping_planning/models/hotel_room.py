# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import date, timedelta

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.fields import Date, Datetime


class HotelRoom(models.Model):
    _inherit = "hotel.room"

    @api.multi
    def action_housekeeping_planning_report(self):
        rooms = self.search([])
        return self.env.ref(
            "hotel_housekeeping_planning"
            ".action_hotel_housekeeping_planning_report"
        ).report_action(rooms)

    @api.multi
    def get_occupation(self, day):
        """day: date object"""
        assert type(day) == date, "day should be of type datetime.date"
        self.ensure_one()

        reservation_lines = self.env["hotel_reservation.line"].search(
            [
                ("line_id.state", "in", ["confirm", "done"]),
                ("reserve", "=", self.id),
                # checkin during the day or sooner
                ("checkin", "<=", Date.to_string(day)),
                # checkout during the day or later
                ("checkout", ">=", Date.to_string(day)),
            ]
        )

        if len(reservation_lines) >= 2:
            return "departure_arrival"
        elif len(reservation_lines) == 0:
            return "free"
        elif Datetime.from_string(reservation_lines.checkin).date() == day:
            return "arrival"
        elif Datetime.from_string(reservation_lines.checkout).date() == day:
            return "departure"
        else:
            return "busy"

    @api.model
    def _get_week(self):
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        return [monday + timedelta(days=i) for i in range(7)]

    @api.multi
    def _get_notes(self):
        self.ensure_one()
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        reservation_lines = (
            self.env["hotel_reservation.line"]
            .search(
                [
                    ("line_id.state", "in", ["confirm", "done"]),
                    ("reserve", "=", self.id),
                    # checkin sunday or sooner
                    ("checkin", "<=", Date.to_string(sunday)),
                    # checkout monday or later
                    ("checkout", ">=", Date.to_string(monday)),
                ]
            )
            .sorted(lambda rl: rl.checkin)
        )
        notes = (rl.line_id.housekeeping_note for rl in reservation_lines)
        notes = (note for note in notes if note)  # remove empty notes (False)
        return "\n".join(notes)

    @api.multi
    def _get_week_occupation(self):
        self.ensure_one()
        week_occupation = [
            self.get_occupation(day) for day in self._get_week()
        ]
        return week_occupation

    @api.multi
    def get_housekeeping_weekly_report_data(self):
        """returns a dictionary with rooms in key and values the daily
            room occupation:
                {
                    # monday to sunday
                    "days": ["2020-06-26", "2020-06-30", ... "2020-07-05"],
                    "rooms": [
                        {
                            "room": "room x (recordset)",
                            "occupation": ["free", "arrival", ... "busy"],
                        }, ...
                    ],
                }
        """
        if not self:
            raise ValidationError(_("No rooms defined in the hotel."))

        week_planning = {
            "days": self._get_week(),
            "rooms": [
                {
                    "room": room,
                    "occupation": room._get_week_occupation(),
                    "notes": room._get_notes(),
                }
                for room in self.sorted()
            ],
        }

        return week_planning

    @api.model
    def get_occupation_acronym(self, occupation):
        occupations = {
            "free": "",
            "arrival": _("A"),
            "departure": _("D"),
            "departure_arrival": _("D/A"),
            "busy": _("O"),
        }
        return occupations[occupation]
