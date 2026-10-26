# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestHousekeeping(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.housekeeping_obj = cls.env["hotel.housekeeping"]
        cls.hotel_act_obj = cls.env["hotel.housekeeping.activities"]
        cls.hotel_act_type_obj = cls.env["hotel.housekeeping.activity.type"]
        cls.housekeeper_id = cls.env.ref("base.user_root")
        cls.inspector_id = cls.env["res.users"].create(
            {
                "name": "Test Inspector",
                "login": "test_inspector",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        cls.hotel_user = cls.env["res.users"].create(
            {
                "name": "Test Hotel User",
                "login": "test_hotel_user",
                "group_ids": [
                    Command.set(
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("vertical_hotel.group_hotel_user").id,
                        ]
                    )
                ],
            }
        )
        cls.root_act_type = cls.hotel_act_type_obj.create({"name": "All Activities"})
        cls.act_type = cls.hotel_act_type_obj.create(
            {"name": "Room Activity", "parent_id": cls.root_act_type.id}
        )
        cls.hotel_act_type = cls.hotel_act_type_obj.create(
            {"name": "Test Room Activity", "parent_id": cls.act_type.id}
        )
        cls.room_type = cls.env["hotel.room.type"].create({"name": "Test Room Type"})
        cls.room = cls.env["hotel.room"].create(
            {
                "name": "Test Room 101",
                "room_categ_id": cls.room_type.id,
                "capacity": 2,
            }
        )
        cls.activity = cls.env["hotel.activity"].create(
            {"name": "Room Cleaning", "categ_id": cls.act_type.id}
        )

    def setUp(self):
        super().setUp()
        # cleaned 08:00-09:30, inspected afterwards
        self.housekeeping = self.housekeeping_obj.create(
            {
                "current_date": "2026-10-10",
                "room_id": self.room.id,
                "clean_type": "daily",
                "inspector_id": self.inspector_id.id,
                "inspect_date_time": "2026-10-10 12:00:00",
            }
        )
        self.hotel_activity = self.hotel_act_obj.create(
            {
                "housekeeping_id": self.housekeeping.id,
                "today_date": "2026-10-10",
                "activity_id": self.activity.id,
                "housekeeper_id": self.housekeeper_id.id,
                "clean_start_time": "2026-10-10 08:00:00",
                "clean_end_time": "2026-10-10 09:30:00",
            }
        )

    def _new_job(self, **vals):
        return self.housekeeping_obj.create(
            dict(
                {
                    "current_date": "2026-10-11",
                    "room_id": self.room.id,
                    "clean_type": "daily",
                    "inspector_id": self.inspector_id.id,
                },
                **vals,
            )
        )

    # Activity types

    def test_name_search(self):
        hotel_activity_type = self.hotel_act_type_obj.name_search("Test Room Activity")
        self.assertEqual(len(hotel_activity_type), 1)
        # A category can be found through its full "Parent / Child" path
        result = self.hotel_act_type_obj.name_search(
            "All Activities / Room Activity / Test Room Activity"
        )
        self.assertEqual(
            [record[0] for record in result],
            self.hotel_act_type.ids,
            "Hierarchical name_search did not match the expected category",
        )
        self.assertEqual(
            self.hotel_act_type.display_name,
            "All Activities / Room Activity / Test Room Activity",
        )

    def test_activity_type_cycle(self):
        with self.assertRaises(ValidationError):
            self.root_act_type.parent_id = self.hotel_act_type

    # Activity lines

    def test_activity_check_clean_start_time(self):
        with self.assertRaises(ValidationError):
            self.hotel_activity.clean_end_time = "2026-10-10 07:00:00"

    def test_activity_default_today_date(self):
        line = self.hotel_act_obj.with_context(default_today_date="2026-10-01").create(
            {
                "housekeeping_id": self.housekeeping.id,
                "housekeeper_id": self.housekeeper_id.id,
                "clean_start_time": "2026-10-10 08:00:00",
                "clean_end_time": "2026-10-10 09:00:00",
            }
        )
        self.assertEqual(str(line.today_date), "2026-10-01")

    def test_inspection_after_cleaning(self):
        # inspection before the cleaning is finished
        with self.assertRaises(ValidationError):
            self.housekeeping.inspect_date_time = "2026-10-10 09:00:00"
        # cleaning extended past the inspection
        with self.assertRaises(ValidationError):
            self.hotel_activity.clean_end_time = "2026-10-10 13:00:00"
        # no inspection time yet: anything goes
        self.housekeeping.inspect_date_time = False
        self.hotel_activity.clean_end_time = "2026-10-10 13:00:00"

    def test_user_can_remove_line(self):
        self.housekeeping.with_user(self.hotel_user).write(
            {"activity_line_ids": [Command.delete(self.hotel_activity.id)]}
        )
        self.assertFalse(self.hotel_activity.exists())

    # Workflow

    def test_action_set_to_dirty(self):
        self.housekeeping.action_set_to_dirty()
        self.assertEqual(self.housekeeping.state, "dirty")
        self.assertTrue(self.hotel_activity.is_dirty)
        self.assertFalse(self.hotel_activity.is_clean)

    def test_room_cancel(self):
        self.housekeeping.room_cancel()
        self.assertEqual(self.housekeeping.state, "cancel")

    def test_room_done(self):
        self.housekeeping.room_clean()
        with self.assertRaises(ValidationError):
            self.housekeeping.room_done()
        self.housekeeping.quality = "excellent"
        self.housekeeping.room_done()
        self.assertEqual(self.housekeeping.state, "done")

    def test_room_done_sets_inspect_time(self):
        job = self._new_job(quality="good")
        job.room_clean()
        job.quality = "good"
        job.room_done()
        self.assertTrue(job.inspect_date_time)

    def test_room_done_multi(self):
        job = self._new_job()
        jobs = self.housekeeping | job
        jobs.room_clean()
        jobs.write({"quality": "good"})
        jobs.room_done()
        self.assertEqual(set(jobs.mapped("state")), {"done"})

    def test_room_inspect(self):
        self.housekeeping.room_cancel()
        self.housekeeping.room_inspect()
        self.assertEqual(self.housekeeping.state, "inspect")

    def test_room_clean(self):
        self.housekeeping.room_clean()
        self.assertEqual(self.housekeeping.state, "clean")
        self.assertTrue(self.hotel_activity.is_clean)

    def test_wrong_transitions(self):
        self.housekeeping.quality = "good"
        # done without cleaning
        with self.assertRaises(UserError):
            self.housekeeping.room_done()
        # inspect again while still open
        with self.assertRaises(UserError):
            self.housekeeping.room_inspect()
        self.housekeeping.room_clean()
        self.housekeeping.quality = "good"
        self.housekeeping.room_done()
        # a finished job stays finished
        for method in ("room_clean", "action_set_to_dirty", "room_cancel"):
            with self.assertRaises(UserError):
                getattr(self.housekeeping, method)()

    def test_display_name(self):
        self.assertEqual(self.housekeeping.display_name, "Test Room 101 (2026-10-10)")

    # Room status

    def test_room_housekeeping_state(self):
        self.assertEqual(self.room.housekeeping_state, "needs_cleaning")
        self.housekeeping.room_clean()
        self.assertEqual(self.room.housekeeping_state, "to_inspect")
        self.housekeeping.quality = "good"
        self.housekeeping.room_done()
        self.assertEqual(self.room.housekeeping_state, "ready")
        # a newer job puts the room back to "needs cleaning"
        job = self._new_job()
        self.assertEqual(self.room.housekeeping_state, "needs_cleaning")
        # ... unless it is cancelled
        job.room_cancel()
        self.assertEqual(self.room.housekeeping_state, "ready")
        self.assertEqual(self.room.housekeeping_count, 2)
        action = self.room.action_view_housekeeping()
        self.assertEqual(
            self.housekeeping_obj.search(action["domain"]), self.housekeeping | job
        )

    def test_room_without_job(self):
        room = self.env["hotel.room"].create(
            {
                "name": "Test Room 102",
                "room_categ_id": self.room_type.id,
                "capacity": 1,
            }
        )
        self.assertFalse(room.housekeeping_state)
        self.assertEqual(room.housekeeping_count, 0)

    # Report

    def _render_report(self, docids, data=None):
        html = self.env["ir.actions.report"]._render_qweb_html(
            "hotel_housekeeping.report_hotel_housekeeping", docids, data=data
        )[0]
        return html.decode()

    def test_report_from_wizard(self):
        self.env.company.external_report_layout_id = self.env.ref(
            "web.external_layout_standard"
        )
        wizard = self.env["hotel.housekeeping.wizard"].create(
            {
                "date_start": "2026-10-01 00:00:00",
                "date_end": "2026-10-31 00:00:00",
                "room_id": self.room.id,
            }
        )
        action = wizard.print_report()
        self.assertEqual(action["type"], "ir.actions.report")
        html = self._render_report(wizard.ids, data=action["data"])
        self.assertIn("Test Room 101", html)
        self.assertIn("Room Cleaning", html)
        self.assertIn("01:30", html)

    def test_report_wizard_period(self):
        wizard = self.env["hotel.housekeeping.wizard"].create(
            {
                "date_start": "2026-11-01 00:00:00",
                "date_end": "2026-11-30 00:00:00",
                "room_id": self.room.id,
            }
        )
        data = {
            "form": {
                "date_start": "2026-11-01 00:00:00",
                "date_end": "2026-11-30 00:00:00",
                "room_id": self.room.id,
            }
        }
        html = self._render_report(wizard.ids, data=data)
        self.assertNotIn("Room Cleaning", html)
        self.assertIn("No activity in this period.", html)
        with self.assertRaises(ValidationError):
            wizard.date_end = "2026-10-01 00:00:00"

    def test_report_from_jobs(self):
        html = self._render_report(self.housekeeping.ids)
        self.assertIn("Test Room 101", html)
        self.assertIn("Room Cleaning", html)
