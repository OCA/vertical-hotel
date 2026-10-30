# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, tagged

# Wait for a selector, fail on any error dialog.
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
class TestReservationAnalysisUi(HttpCase):
    def test_analysis_pivot(self):
        selector = ".o_pivot_view"
        self.browser_js(
            "/odoo/action-report_hotel_reservation.action_report_hotel_reservation_status",
            WAIT_FOR % {"selector": selector},
            login="admin",
        )
