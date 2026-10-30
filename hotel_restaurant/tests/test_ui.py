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
class TestRestaurantUi(HttpCase):
    def _assert_renders(self, url, selector, then=""):
        self.browser_js(
            url, WAIT_FOR % {"selector": selector, "then": then}, login="admin"
        )

    def test_booking_form(self):
        self._assert_renders(
            "/odoo/action-hotel_restaurant.open_view_hotel_restaurant_reservation_form_tree/new",
            ".o_form_view .o_field_widget[name=table_nos_ids]",
        )

    def test_order_form(self):
        self._assert_renders(
            "/odoo/action-hotel_restaurant.open_view_hotel_restaurant_order_form_tree/new",
            ".o_form_view .o_field_widget[name=order_list_ids]",
        )

    def test_report_wizard(self):
        self._assert_renders(
            "/odoo",
            ".o_main_navbar",
            """
            await odoo.__WOWL_DEBUG__.root.env.services.action.doAction(
                "hotel_restaurant.action_folio_rest_reservation"
            );
            await waitFor(".modal .o_field_widget[name=date_start]");
            """,
        )
