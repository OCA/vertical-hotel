# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime

from odoo.tests import common


class TestHousekeeping(common.TransactionCase):
    def setUp(self):
        super(TestHousekeeping, self).setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self.housekeeping_obj = self.env["hotel.housekeeping"]
        self.hotel_act_obj = self.env["hotel.housekeeping.activities"]
        self.hotel_act_type_obj = self.env["hotel.housekeeping.activity.type"]
        self.housekeeper_id = self.env.ref("base.user_root")
        self.inspector_id = self.env.ref("base.user_demo")
        self.act_type = self.env.ref(
            "hotel_housekeeping.hotel_housekeeping_activity_type_1"
        )
        self.room = self.env.ref("hotel.hotel_room_0")
        self.activity = self.env.ref("hotel_housekeeping.hotel_room_activities_1")
        self.activity_type = self.env["hotel.housekeeping.activity.type"]

        cur_date = datetime.now().strftime("%Y-%m-21 %H:%M:%S")
        cur_date1 = datetime.now().strftime("%Y-%m-23 %H:%M:%S")

        self.housekeeping = self.housekeeping_obj.create(
            {
                "current_date": time.strftime("%Y-%m-%d"),
                "room_id": self.room.id,
                "clean_type": "daily",
                "inspector_id": self.inspector_id.id,
                "state": "dirty",
                "quality": "excellent",
                "inspect_date_time": cur_date,
            }
        )

        self.hotel_act_type = self.hotel_act_type_obj.create(
            {"name": "Test Room Activity", "activity_id": self.act_type.id}
        )

        self.hotel_activity = self.hotel_act_obj.create(
            {
                "housekeeping_id": self.housekeeping.id,
                "today_date": time.strftime("%Y-%m-%d"),
                "activity_id": self.activity.id,
                "housekeeper_id": self.housekeeper_id.id,
                "clean_start_time": cur_date,
                "clean_end_time": cur_date1,
            }
        )

        self.hotel_act_type.name_get()
        hotel_activity_type = self.hotel_act_type_obj.name_search("Test Room Activity")
        self.assertEqual(
            len(hotel_activity_type),
            1,
            "Incorrect search number result for name_search",
        )

    def test_name_search(self):
        self.activity_type = self.env["hotel.housekeeping.activity.type"].create(
            {
                "name": "Test",
            }
        )
        self.env["hotel.housekeeping.activity.type"].name_search(
            "All Activities / Test Room Activity", [], "not like", None
        )

    def test_activity_check_clean_start_time(self):
        self.hotel_activity._check_clean_start_time()

    def test_activity_default_get(self):
        fields = ["room_id", "today_date"]
        self.hotel_activity.default_get(fields)

    def test_action_set_to_dirty(self):
        self.housekeeping.action_set_to_dirty()

    def test_room_cancel(self):
        self.housekeeping.room_cancel()
        self.assertEqual(self.housekeeping.state == "cancel", True)

    def test_room_done(self):
        self.housekeeping.room_done()
        self.assertEqual(self.housekeeping.state == "done", True)

    def test_room_inspect(self):
        self.housekeeping.room_inspect()
        self.assertEqual(self.housekeeping.state == "inspect", True)

    def test_room_clean(self):
        self.housekeeping.room_clean()
        self.assertEqual(self.housekeeping.state == "clean", True)
