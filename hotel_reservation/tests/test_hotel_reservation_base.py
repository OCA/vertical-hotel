from datetime import datetime, timedelta

from odoo.tests import common

_TODAY = datetime.today().replace(hour=10, minute=10, second=0)
_WEEKDAYS = {
    "monday": _TODAY - timedelta(days=_TODAY.weekday()),
    "tuesday": _TODAY - timedelta(days=_TODAY.weekday() - 1),
    "wednesday": _TODAY - timedelta(days=_TODAY.weekday() - 2),
    "thursday": _TODAY - timedelta(days=_TODAY.weekday() - 3),
    "friday": _TODAY - timedelta(days=_TODAY.weekday() - 4),
    "saturday": _TODAY - timedelta(days=_TODAY.weekday() - 5),
    "sunday": _TODAY - timedelta(days=_TODAY.weekday() - 6),
}


class TestReservationBase(common.TransactionCase):
    def setUp(self):
        super(TestReservationBase, self).setUp()
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
            }
        )
        self.reservation_1_line = self.env["hotel_reservation.line"].create(
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
            }
        )
        self.reservation_2_line = self.env["hotel_reservation.line"].create(
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
                "state": "draft",
            }
        )
        self.reservation_3_line = self.env["hotel_reservation.line"].create(
            {
                "line_id": self.reservation_3.id,
                "categ_id": self.ref("hotel.hotel_room_type_2"),
                "reserve": [(6, 0, [self.room_3.id])],
            }
        )
