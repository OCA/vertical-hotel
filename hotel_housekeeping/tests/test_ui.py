# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, tagged

# Open a page, wait for a selector, fail on any error dialog.
WAIT_FOR = """
(async () => {
    const t0 = Date.now();
    while (!document.querySelector(%(selector)r)) {
        const dialog = document.querySelector(".o_error_dialog");
        if (dialog) {
            throw new Error(dialog.innerText.slice(0, 500));
        }
        if (Date.now() - t0 > 20000) {
            throw new Error("timeout waiting for " + %(selector)r);
        }
        await new Promise((resolve) => setTimeout(resolve, 250));
    }
    console.log("test successful");
})();
"""


@tagged("post_install", "-at_install")
class TestHousekeepingUi(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        room_type = cls.env["hotel.room.type"].create({"name": "UI Room Type"})
        cls.room = cls.env["hotel.room"].create(
            {"name": "UI Room", "capacity": 2, "room_categ_id": room_type.id}
        )
        cls.job = cls.env["hotel.housekeeping"].create(
            {
                "room_id": cls.room.id,
                "clean_type": "daily",
                "inspector_id": cls.env.ref("base.user_admin").id,
            }
        )

    def _assert_renders(self, url, selector):
        self.browser_js(url, WAIT_FOR % {"selector": selector}, login="admin")

    def test_housekeeping_board(self):
        self._assert_renders(
            "/odoo/action-hotel_housekeeping.open_hotel_housekeeping_form_tree",
            ".o_kanban_view .o_kanban_record:not(.o_kanban_ghost)",
        )

    def test_housekeeping_form(self):
        self._assert_renders(
            "/odoo/action-hotel_housekeeping.open_hotel_housekeeping_form_tree"
            f"/{self.job.id}",
            ".o_form_view .o_field_widget[name=activity_line_ids]",
        )

    def test_room_form_housekeeping(self):
        self._assert_renders(
            f"/odoo/action-vertical_hotel.action_hotel_room_form/{self.room.id}",
            ".o_form_view .o_field_widget[name=housekeeping_state]",
        )

    def test_room_board_housekeeping(self):
        self._assert_renders(
            "/odoo/action-vertical_hotel.action_hotel_room_form",
            ".o_kanban_view .o_kanban_record .o_field_widget[name=housekeeping_state]",
        )

    def test_report_wizard(self):
        # dialog actions are not restored from the URL: open it with doAction
        self.browser_js(
            "/odoo",
            """
            (async () => {
                const t0 = Date.now();
                while (!odoo.__WOWL_DEBUG__?.root?.env) {
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
                const env = odoo.__WOWL_DEBUG__.root.env;
                await env.services.action.doAction(
                    "hotel_housekeeping.action_hotel_housekeeping_wizard"
                );
                while (!document.querySelector(
                    ".modal .o_field_widget[name=room_id]"
                )) {
                    if (Date.now() - t0 > 20000) {
                        throw new Error("wizard did not open");
                    }
                    await new Promise((resolve) => setTimeout(resolve, 250));
                }
                const footer = document.querySelector(".modal-footer");
                if (!footer.querySelector("button[name=print_report]")) {
                    throw new Error("no Print button");
                }
                console.log("test successful");
            })();
            """,
            login="admin",
        )
