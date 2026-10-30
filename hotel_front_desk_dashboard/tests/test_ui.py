# Copyright (C) 2026-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from datetime import timedelta

from odoo import fields
from odoo.fields import Command
from odoo.tests import HttpCase, tagged

from .test_dashboard import TILES

DASHBOARD_URL = (
    "/odoo/action-hotel_front_desk_dashboard.action_hotel_front_desk_dashboard"
)

# Helpers shared by the browser tests: wait for a selector and fail on any
# error dialog.
HELPERS = """
const failIfError = () => {
    const dialog = document.querySelector(".o_error_dialog");
    if (dialog) {
        throw new Error(dialog.innerText.slice(0, 800));
    }
    // a failed data load shows an alert instead of a dialog
    const alert = document.querySelector(".o_hotel_front_desk_dashboard .alert-danger");
    if (alert) {
        throw new Error("dashboard: " + alert.innerText);
    }
};
const waitFor = async (selector) => {
    const t0 = Date.now();
    while (!document.querySelector(selector)) {
        failIfError();
        if (Date.now() - t0 > 20000) {
            throw new Error("timeout waiting for " + selector);
        }
        await new Promise((resolve) => setTimeout(resolve, 200));
    }
    return document.querySelector(selector);
};
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
"""


@tagged("post_install", "-at_install")
class TestFrontDeskDashboardUi(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        room_type = cls.env["hotel.room.type"].create({"name": "UI Desk Type"})
        cls.room = cls.env["hotel.room"].create(
            {"name": "UI-DESK-1", "capacity": 2, "room_categ_id": room_type.id}
        )
        partner = cls.env["res.partner"].create({"name": "UI Desk Guest"})
        now = fields.Datetime.now().replace(microsecond=0)
        start, end = now + timedelta(days=3), now + timedelta(days=4)
        cls.folio = cls.env["hotel.folio"].create(
            {
                "partner_id": partner.id,
                "checkin_date": start,
                "checkout_date": end,
                "room_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.room.product_id.id,
                            "checkin_date": start,
                            "checkout_date": end,
                            "product_uom_qty": 1,
                        }
                    )
                ],
            }
        )
        cls.folio.action_confirm()

    def _run(self, code):
        self.browser_js(
            DASHBOARD_URL,
            "(async () => {\n"
            + HELPERS
            + "\n"
            + code
            + "\nconsole.log('test successful');})();",
            login="admin",
        )

    def test_dashboard_tiles(self):
        """The dashboard opens and every tile drills down to a list."""
        self._run(
            """
            await waitFor(".o_hotel_front_desk_dashboard .o_hfd_tile");
            const env = odoo.__WOWL_DEBUG__.root.env;
            for (const tile of TILES_JSON) {
                const action = await env.services.orm.call(
                    "hotel.dashboard", "get_tile_action", [tile]
                );
                await env.services.action.doAction(action);
                await waitFor(".o_list_view");
                failIfError();
            }
            """.replace("TILES_JSON", json.dumps(list(TILES)))
        )

    def test_dashboard_clicks(self):
        """Clicking a tile, refreshing, toggling auto-refresh and searching
        a guest work from the screen itself."""
        self._run(
            """
            const tile = await waitFor(".o_hotel_front_desk_dashboard .o_hfd_tile");
            document.querySelector("#o_hfd_auto").click();
            [...document.querySelectorAll(".o_hotel_front_desk_dashboard button")]
                .find((b) => b.innerText.includes("Refresh"))?.click();
            await sleep(500);
            failIfError();
            const search = document.querySelector(".o_hfd_search input");
            search.value = "UI Desk Guest";
            search.dispatchEvent(new Event("input", {bubbles: true}));
            const hit = await waitFor(".o_hfd_search_hit");
            hit.click();
            await waitFor(".o_form_view");
            failIfError();
            history.back();
            await waitFor(".o_hotel_front_desk_dashboard .o_hfd_tile");
            document.querySelector(".o_hotel_front_desk_dashboard .o_hfd_tile").click();
            await waitFor(".o_list_view");
            failIfError();
            """
        )
