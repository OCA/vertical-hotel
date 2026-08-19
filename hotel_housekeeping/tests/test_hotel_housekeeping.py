# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime

from odoo.tests import common


class TestHousekeeping(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self.housekeeping_obj = self.env["hotel.housekeeping"]
        self.hotel_act_obj = self.env["hotel.housekeeping.activities"]
        self.hotel_act_type_obj = self.env["hotel.housekeeping.activity.type"]
        self.housekeeper_id = self.env.ref("base.user_root")
        self.inspector_id = self.env["res.users"].create(
            {
                "name": "Test Inspector",
                "login": "test_inspector",
                "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        self.root_act_type = self.hotel_act_type_obj.create({"name": "All Activities"})
        self.act_type = self.hotel_act_type_obj.create(
            {"name": "Room Activity", "parent_id": self.root_act_type.id}
        )
        self.room_type = self.env["hotel.room.type"].create({"name": "Test Room Type"})
        self.room = self.env["hotel.room"].create(
            {
                "name": "Test Room 101",
                "room_categ_id": self.room_type.id,
                "capacity": 2,
            }
        )
        self.activity = self.env["hotel.activity"].create(
            {"name": "Room Cleaning", "categ_id": self.act_type.id}
        )

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
            {"name": "Test Room Activity", "parent_id": self.act_type.id}
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

        self.hotel_act_type._compute_display_name()
        hotel_activity_type = self.hotel_act_type_obj.name_search("Test Room Activity")
        self.assertEqual(
            len(hotel_activity_type),
            1,
            "Incorrect search number result for name_search",
        )

    def test_name_search(self):
        self.activity_type = self.hotel_act_type_obj.create(
            {
                "name": "Test",
            }
        )
        # A category can be found through its full "Parent / Child" path
        result = self.hotel_act_type_obj.name_search(
            "All Activities / Room Activity / Test Room Activity"
        )
        self.assertEqual(
            [record[0] for record in result],
            self.hotel_act_type.ids,
            "Hierarchical name_search did not match the expected category",
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
