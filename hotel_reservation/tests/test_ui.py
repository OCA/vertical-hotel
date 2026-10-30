# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, tagged

# Wait for a selector (failing on any error dialog), run ``then``, report.
WAIT_FOR = """
(async () => {
    const waitFor = async (selector) => {
        const t0 = Date.now();
        while (!document.querySelector(selector)) {
            const dialog = document.querySelector(".o_error_dialog");
            if (dialog) {
                throw new Error(dialog.innerText.slice(0, 500));
            }
            if (Date.now() - t0 > 20000) {
                throw new Error("timeout waiting for " + selector);
            }
            await new Promise((resolve) => setTimeout(resolve, 250));
        }
        return document.querySelector(selector);
    };
    await waitFor(%(selector)r);
    %(then)s
    console.log("test successful");
})();
"""


@tagged("post_install", "-at_install")
class TestReservationUi(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        room_type = cls.env["hotel.room.type"].create({"name": "UI Room Type"})
        cls.env["hotel.room"].create(
            {"name": "UI Room", "capacity": 2, "room_categ_id": room_type.id}
        )

    def _assert_renders(self, url, selector, then=""):
        self.browser_js(
            url, WAIT_FOR % {"selector": selector, "then": then}, login="admin"
        )

    def test_reservation_form(self):
        self._assert_renders(
            "/odoo/action-hotel_reservation.action_hotel_reservation_tree_all/new",
            ".o_form_view .o_field_widget[name=reservation_line]",
        )

    def test_summary_quick_reservation(self):
        # a free day of the summary opens the quick reservation dialog
        self._assert_renders(
            "/odoo/action-hotel_reservation.action_hotel_reservation_summary",
            ".o_room_summary td.o_room_summary_free",
            """
            (await waitFor(".o_room_summary td.o_room_summary_free")).click();
            await waitFor(".modal .o_field_widget[name=partner_id]");
            if (!document.querySelector(".modal-footer button[name=room_reserve]")) {
                throw new Error("no Save button");
            }
            """,
        )

    def test_report_wizard(self):
        self._assert_renders(
            "/odoo",
            ".o_main_navbar",
            """
            await odoo.__WOWL_DEBUG__.root.env.services.action.doAction(
                "hotel_reservation.action_hotel_reservation_wizard"
            );
            await waitFor(".modal .o_field_widget[name=date_start]");
            """,
        )
