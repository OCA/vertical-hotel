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
class TestHotelUi(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        room_type = cls.env["hotel.room.type"].create({"name": "UI Room Type"})
        cls.room = cls.env["hotel.room"].create(
            {
                "name": "UI Room",
                "capacity": 2,
                "isroom": True,
                "room_categ_id": room_type.id,
            }
        )

    def _assert_renders(self, url, selector):
        self.browser_js(url, WAIT_FOR % {"selector": selector}, login="admin")

    def test_room_board(self):
        self._assert_renders(
            "/odoo/action-vertical_hotel.action_hotel_room_form",
            ".o_kanban_view .o_kanban_record:not(.o_kanban_ghost)",
        )

    def test_room_form(self):
        self._assert_renders(
            f"/odoo/action-vertical_hotel.action_hotel_room_form/{self.room.id}",
            ".o_form_view .o_field_widget[name=room_categ_id]",
        )

    def test_folio_form(self):
        self._assert_renders(
            "/odoo/action-vertical_hotel.open_hotel_folio1_form_tree_all/new",
            ".o_form_view .o_field_widget[name=room_line_ids]",
        )
