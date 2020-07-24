# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime, timedelta

from odoo.fields import Datetime

from odoo.addons.hotel_reservation.tests import test_hotel_reservation_base


class TestReservationSummary(test_hotel_reservation_base.TestReservationBase):
    def test_compute_headers(self):
        today = datetime.today()
        today_plus_1 = today + timedelta(days=1)
        today_plus_2 = today + timedelta(days=2)
        today_plus_3 = today + timedelta(days=3)

        expected_headers = [
            "Rooms",
            today.strftime("%a %d %b"),
            today_plus_1.strftime("%a %d %b"),
            today_plus_2.strftime("%a %d %b"),
        ]
        computed_headers = self.env[
            "hotel.room.reservation.summary.test"
        ]._compute_headers(today, today_plus_3)
        self.assertEquals(expected_headers, computed_headers)

    def test_get_room_status(self):
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        tuesday = monday + timedelta(days=1)
        sunday = monday + timedelta(days=6)

        ReservationLine = self.env["hotel_reservation.line"]

        self.assertEquals(
            self.room_1.get_room_status(monday), ("free", ReservationLine)
        )
        self.assertEquals(
            self.room_1.get_room_status(tuesday),
            ("busy", self.reservation_1_line),
        )
        self.assertEquals(
            self.room_1.get_room_status(sunday), ("free", ReservationLine)
        )

        self.assertEquals(
            self.room_3.get_room_status(monday), ("free", ReservationLine)
        )
        self.assertEquals(
            self.room_3.get_room_status(tuesday),
            ("draft", self.reservation_3_line),
        )
        self.assertEquals(
            self.room_3.get_room_status(sunday), ("free", ReservationLine)
        )

    def test_get_room_daily_summary(self):
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        tuesday = monday + timedelta(days=1)
        thursday = monday + timedelta(days=3)
        sunday = monday + timedelta(days=6)

        self.assertEquals(
            self.room_1.get_room_daily_summary(monday),
            {
                "date": Datetime.to_string(monday),
                "state": "free",
                "state_text": "",
                "room_id": self.room_1.id,
                "reservation_id": False,
            },
        )
        self.assertEquals(
            self.room_1.get_room_daily_summary(tuesday),
            {
                "date": Datetime.to_string(tuesday),
                "state": "busy",
                "state_text": "A 10:10",
                "room_id": self.room_1.id,
                "reservation_id": self.reservation_1.id,
            },
        )
        self.assertEquals(
            self.room_1.get_room_daily_summary(thursday),
            {
                "date": Datetime.to_string(thursday),
                "state": "busy",
                "state_text": "10:10 D/A 10:10",
                "room_id": self.room_1.id,
                "reservation_id": self.reservation_2.id,
            },
        )
        self.assertEquals(
            self.room_1.get_room_daily_summary(sunday),
            {
                "date": Datetime.to_string(sunday),
                "state": "free",
                "state_text": "",
                "room_id": self.room_1.id,
                "reservation_id": False,
            },
        )

        self.assertEquals(
            self.room_3.get_room_daily_summary(monday),
            {
                "date": Datetime.to_string(monday),
                "state": "free",
                "state_text": "",
                "room_id": self.room_3.id,
                "reservation_id": False,
            },
        )
        self.assertEquals(
            self.room_3.get_room_daily_summary(tuesday),
            {
                "date": Datetime.to_string(tuesday),
                "state": "draft",
                "state_text": "A 10:10",
                "room_id": self.room_3.id,
                "reservation_id": self.reservation_3.id,
            },
        )
        self.assertEquals(
            self.room_3.get_room_daily_summary(thursday),
            {
                "date": Datetime.to_string(thursday),
                "state": "draft",
                "state_text": self.reservation_3.partner_id.name,
                "room_id": self.room_3.id,
                "reservation_id": self.reservation_3.id,
            },
        )
        self.assertEquals(
            self.room_3.get_room_daily_summary(sunday),
            {
                "date": Datetime.to_string(sunday),
                "state": "free",
                "state_text": "",
                "room_id": self.room_3.id,
                "reservation_id": False,
            },
        )
