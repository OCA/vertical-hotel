# See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo.fields import Datetime
from odoo.tests import common

_TODAY = datetime.today().replace(hour=10)
_WEEKDAYS = {
    "monday": _TODAY - timedelta(days=_TODAY.weekday()),
    "tuesday": _TODAY - timedelta(days=_TODAY.weekday() - 1),
    "wednesday": _TODAY - timedelta(days=_TODAY.weekday() - 2),
    "thursday": _TODAY - timedelta(days=_TODAY.weekday() - 3),
    "friday": _TODAY - timedelta(days=_TODAY.weekday() - 4),
    "saturday": _TODAY - timedelta(days=_TODAY.weekday() - 5),
    "sunday": _TODAY - timedelta(days=_TODAY.weekday() - 6),
}

_ROOM_1_OCCUPATION = [
    "free",
    "arrival",
    "busy",
    "departure_arrival",
    "busy",
    "departure",
    "free",
]
_ROOM_2_OCCUPATION = [
    "free",
    "free",
    "free",
    "arrival",
    "busy",
    "departure",
    "free",
]
_ROOM_3_OCCUPATION = [
    "free",
    "arrival",
    "busy",
    "busy",
    "busy",
    "departure",
    "free",
]


class TestHousekeeping(common.TransactionCase):
    def setUp(self):
        super(TestHousekeeping, self).setUp()
        self.browse_ref("base.partner_root").tz = "UTC"
        self.room_1 = self.env["hotel.room"].create(
            {
                "name": "test-room-1",
                "isroom": True,
                "room_categ_id": self.ref("hotel.hotel_room_type_1"),
                "list_price": 100.0,
                "capacity": 2,
            }
        )
        self.room_2 = self.env["hotel.room"].create(
            {
                "name": "test-room-2",
                "isroom": True,
                "room_categ_id": self.ref("hotel.hotel_room_type_1"),
                "list_price": 110.0,
                "capacity": 2,
            }
        )
        self.room_3 = self.env["hotel.room"].create(
            {
                "name": "test-room-3",
                "isroom": True,
                "room_categ_id": self.ref("hotel.hotel_room_type_2"),
                "list_price": 150.0,
                "capacity": 3,
            }
        )

        self.reservation_1 = self.env["hotel.reservation"].create(
            {
                "date_order": datetime.today() - timedelta(weeks=2),
                "checkin": _WEEKDAYS["tuesday"],
                "checkout": _WEEKDAYS["thursday"],
                "partner_id": self.ref("base.res_partner_2"),
                "pricelist_id": self.ref("product.list0"),
                "state": "confirm",
                "housekeeping_note": "fix leaking tap",
            }
        )
        self.env["hotel_reservation.line"].create(
            {
                "line_id": self.reservation_1.id,
                "categ_id": self.ref("hotel.hotel_room_type_1"),
                "reserve": [(6, 0, [self.room_1.id])],
            }
        )

        self.reservation_2 = self.env["hotel.reservation"].create(
            {
                "date_order": datetime.today() - timedelta(weeks=2),
                "checkin": _WEEKDAYS["thursday"],
                "checkout": _WEEKDAYS["saturday"],
                "partner_id": self.ref("base.res_partner_3"),
                "pricelist_id": self.ref("product.list0"),
                "state": "confirm",
                "housekeeping_note": "add bed in room 1",
            }
        )
        self.env["hotel_reservation.line"].create(
            {
                "line_id": self.reservation_2.id,
                "categ_id": self.ref("hotel.hotel_room_type_1"),
                "reserve": [(6, 0, [self.room_1.id, self.room_2.id])],
            }
        )

        self.reservation_3 = self.env["hotel.reservation"].create(
            {
                "date_order": datetime.today() - timedelta(weeks=2),
                "checkin": _WEEKDAYS["tuesday"],
                "checkout": _WEEKDAYS["saturday"],
                "partner_id": self.ref("base.res_partner_4"),
                "pricelist_id": self.ref("product.list0"),
                "state": "confirm",
            }
        )
        self.env["hotel_reservation.line"].create(
            {
                "line_id": self.reservation_3.id,
                "categ_id": self.ref("hotel.hotel_room_type_2"),
                "reserve": [(6, 0, [self.room_3.id])],
            }
        )

    def test_get_occupation(self):
        self.assertEquals(
            "free", self.room_1.get_occupation(_WEEKDAYS["monday"].date())
        )
        self.assertEquals(
            "arrival", self.room_1.get_occupation(_WEEKDAYS["tuesday"].date())
        )
        self.assertEquals(
            "busy", self.room_1.get_occupation(_WEEKDAYS["wednesday"].date())
        )
        self.assertEquals(
            "departure_arrival",
            self.room_1.get_occupation(_WEEKDAYS["thursday"].date()),
        )
        self.assertEquals(
            "busy", self.room_1.get_occupation(_WEEKDAYS["friday"].date())
        )
        self.assertEquals(
            "departure",
            self.room_1.get_occupation(_WEEKDAYS["saturday"].date()),
        )
        self.assertEquals(
            "free", self.room_1.get_occupation(_WEEKDAYS["sunday"].date())
        )

    def test_get_week_occupation(self):
        self.assertEquals(
            _ROOM_1_OCCUPATION, self.room_1._get_week_occupation()
        )
        self.assertEquals(
            _ROOM_2_OCCUPATION, self.room_2._get_week_occupation()
        )
        self.assertEquals(
            _ROOM_3_OCCUPATION, self.room_3._get_week_occupation()
        )

    def test_get_notes(self):
        date_1 = Datetime.from_string(self.reservation_1.checkin)
        date_str_1 = date_1.strftime("%a %d %b")

        date_2 = Datetime.from_string(self.reservation_2.checkin)
        date_str_2 = date_2.strftime("%a %d %b")

        expected_room_1 = "\n".join(
            [
                "{}: {}".format(date_str_1, "fix leaking tap"),
                "{}: {}".format(date_str_2, "add bed in room 1"),
            ]
        )
        self.assertEquals(expected_room_1, self.room_1._get_notes())
        self.assertEquals(
            "{}: {}".format(date_str_2, "add bed in room 1"),
            self.room_2._get_notes(),
        )
        self.assertEquals("", self.room_3._get_notes())

    def test_get_housekeeping_weekly_report_data(self):
        date_1 = Datetime.from_string(self.reservation_1.checkin)
        date_str_1 = date_1.strftime("%a %d %b")

        date_2 = Datetime.from_string(self.reservation_2.checkin)
        date_str_2 = date_2.strftime("%a %d %b")

        expected_room_1_note = "\n".join(
            [
                "{}: {}".format(date_str_1, "fix leaking tap"),
                "{}: {}".format(date_str_2, "add bed in room 1"),
            ]
        )

        expected_weekly_planning = {
            "days": [day.date() for day in sorted(_WEEKDAYS.values())],
            "rooms": [
                {
                    "room": self.room_1,
                    "occupation": _ROOM_1_OCCUPATION,
                    "notes": expected_room_1_note,
                },
                {
                    "room": self.room_2,
                    "occupation": _ROOM_2_OCCUPATION,
                    "notes": "{}: {}".format(date_str_2, "add bed in room 1"),
                },
                {
                    "room": self.room_3,
                    "occupation": _ROOM_3_OCCUPATION,
                    "notes": "",
                },
            ],
        }

        rooms = self.room_1 | self.room_2 | self.room_3
        computed_weekly_planning = rooms.get_housekeeping_weekly_report_data()
        self.assertEquals(expected_weekly_planning, computed_weekly_planning)
