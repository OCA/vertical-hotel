# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo.fields import Date, Datetime

from odoo.addons.hotel_reservation.tests import test_hotel_reservation_base


class TestReservationSummary(test_hotel_reservation_base.TestReservationBase):
    def test_compute_headers(self):
        today = date.today()
        today_plus_1 = today + timedelta(days=1)
        today_plus_2 = today + timedelta(days=2)
        today_plus_3 = today + timedelta(days=3)

        summary = self.env["hotel.room.reservation.summary.test"].create(
            {
                "date_from": Date.to_string(today),
                "date_to": Date.to_string(today_plus_3),
            }
        )

        expected_headers = [
            "Rooms",
            today.strftime("%a %d %b"),
            today_plus_1.strftime("%a %d %b"),
            today_plus_2.strftime("%a %d %b"),
        ]
        computed_headers = summary._compute_headers(today, today_plus_3)
        self.assertEquals(expected_headers, computed_headers)

    def test_compute_room_summary(self):
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        tuesday = monday + timedelta(days=1)
        sunday = monday + timedelta(days=6)

        expected_room_summary = [
            {
                "headers": [
                    "Rooms",
                    (monday + timedelta(days=0)).strftime("%a %d %b"),
                    (monday + timedelta(days=1)).strftime("%a %d %b"),
                    (monday + timedelta(days=2)).strftime("%a %d %b"),
                    (monday + timedelta(days=3)).strftime("%a %d %b"),
                    (monday + timedelta(days=4)).strftime("%a %d %b"),
                    (monday + timedelta(days=5)).strftime("%a %d %b"),
                    (monday + timedelta(days=6)).strftime("%a %d %b"),
                ],
                "rows": [
                    {
                        "name": self.room_1.name,
                        "value": [
                            {
                                "date": Datetime.to_string(monday),
                                "state": "free",
                                "state_text": "",
                                "room_id": self.room_1.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=1)
                                ),
                                "state": "busy",
                                "state_text": "A 10:10",
                                "room_id": self.room_1.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=2)
                                ),
                                "state": "busy",
                                "state_text": self.reservation_1.partner_id.name,
                                "room_id": self.room_1.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=3)
                                ),
                                "state": "busy",
                                "state_text": "10:10 D/A 10:10",
                                "room_id": self.room_1.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=4)
                                ),
                                "state": "busy",
                                "state_text": self.reservation_2.partner_id.name,
                                "room_id": self.room_1.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=5)
                                ),
                                "state": "busy",
                                "state_text": "10:10 D",
                                "room_id": self.room_1.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=6)
                                ),
                                "state": "free",
                                "state_text": "",
                                "room_id": self.room_1.id,
                            },
                        ],
                    },
                    {
                        "name": self.room_2.name,
                        "value": [
                            {
                                "date": Datetime.to_string(monday),
                                "state": "free",
                                "state_text": "",
                                "room_id": self.room_2.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=1)
                                ),
                                "state": "free",
                                "state_text": "",
                                "room_id": self.room_2.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=2)
                                ),
                                "state": "free",
                                "state_text": "",
                                "room_id": self.room_2.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=3)
                                ),
                                "state": "busy",
                                "state_text": "A 10:10",
                                "room_id": self.room_2.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=4)
                                ),
                                "state": "busy",
                                "state_text": self.reservation_2.partner_id.name,
                                "room_id": self.room_2.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=5)
                                ),
                                "state": "busy",
                                "state_text": "10:10 D",
                                "room_id": self.room_2.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=6)
                                ),
                                "state": "free",
                                "state_text": "",
                                "room_id": self.room_2.id,
                            },
                        ],
                    },
                    {
                        "name": self.room_3.name,
                        "value": [
                            {
                                "date": Datetime.to_string(monday),
                                "state": "free",
                                "state_text": "",
                                "room_id": self.room_3.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=1)
                                ),
                                "state": "draft",
                                "state_text": "A 10:10",
                                "room_id": self.room_3.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=2)
                                ),
                                "state": "draft",
                                "state_text": self.reservation_3.partner_id.name,
                                "room_id": self.room_3.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=3)
                                ),
                                "state": "draft",
                                "state_text": self.reservation_3.partner_id.name,
                                "room_id": self.room_3.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=4)
                                ),
                                "state": "draft",
                                "state_text": self.reservation_3.partner_id.name,
                                "room_id": self.room_3.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=5)
                                ),
                                "state": "draft",
                                "state_text": "10:10 D",
                                "room_id": self.room_3.id,
                            },
                            {
                                "date": Datetime.to_string(
                                    monday + timedelta(days=6)
                                ),
                                "state": "free",
                                "state_text": "",
                                "room_id": self.room_3.id,
                            },
                        ],
                    },
                ],
            }
        ]

        summary = self.env["hotel.room.reservation.summary.test"].create(
            {
                "date_from": Date.to_string(tuesday),
                "date_to": Date.to_string(sunday),
            }
        )
        rooms = self.room_1 | self.room_2 | self.room_3
        summary._compute_room_summary(rooms=rooms)

        # pylint: disable=eval-used,eval-referenced
        room_summary = eval(summary.room_summary)
        self.assertEquals(room_summary, expected_room_summary)
