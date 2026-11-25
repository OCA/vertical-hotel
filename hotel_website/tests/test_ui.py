# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, tagged

# Wait for a selector and fail on any error page.
HELPERS = """
const waitFor = async (selector) => {
    const t0 = Date.now();
    while (!document.querySelector(selector)) {
        if (document.title.includes("Internal Server Error")) {
            throw new Error("server error page");
        }
        if (Date.now() - t0 > 20000) {
            throw new Error("timeout waiting for " + selector);
        }
        await new Promise((resolve) => setTimeout(resolve, 200));
    }
    return document.querySelector(selector);
};
"""


@tagged("post_install", "-at_install")
class TestHotelWebsiteUi(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("base.default_website")
        cls.room_type = cls.env["hotel.room.type"].create({"name": "UI Family Room"})
        cls.room = cls.env["hotel.room"].create(
            {
                "name": "UI-F1",
                "room_categ_id": cls.room_type.id,
                "capacity": 4,
                "list_price": 100.0,
            }
        )
        if not cls.env["product.pricelist"].search([], limit=1):
            cls.env["product.pricelist"].create({"name": "UI Pricelist"})
        cls.checkin = cls.website._hotel_today() + timedelta(days=30)
        cls.checkout = cls.checkin + timedelta(days=2)

    def _run(self, url, code):
        self.browser_js(
            url,
            "(async () => {\n"
            + HELPERS
            + "\n"
            + code
            + "\nconsole.log('test successful');})();",
        )

    def test_dates_widget(self):
        """The booking bar keeps departure after arrival."""
        self._run(
            "/rooms",
            """
            const bar = await waitFor(".o_hotel_stay_dates");
            // let the interactions start
            await new Promise((resolve) => setTimeout(resolve, 1000));
            const checkin = bar.querySelector("input[name='checkin']");
            const checkout = bar.querySelector("input[name='checkout']");
            checkin.value = "2099-03-10";
            checkin.dispatchEvent(new Event("change", {bubbles: true}));
            await new Promise((resolve) => setTimeout(resolve, 200));
            if (checkout.min !== "2099-03-11") {
                throw new Error("checkout min not updated: " + checkout.min);
            }
            """,
        )

    def test_booking_flow(self):
        """A visitor books a room type with two accompanying guests; the
        request reaches the front desk with its guests."""
        checkin = fields.Date.to_string(self.checkin)
        checkout = fields.Date.to_string(self.checkout)
        # The stay (cart) lives in the visitor's session, which browser_js
        # creates: add the room from the browser, then open the guest details
        # in a frame of the same session, where the page's interactions run.
        self._run(
            f"/rooms?checkin={checkin}&checkout={checkout}",
            """
            const reserve = await waitFor(".o_hotel_reserve_form");
            const added = await fetch(reserve.action, {
                method: "POST",
                body: new FormData(reserve),
            });
            if (!added.url.includes("/rooms/cart")) {
                throw new Error("room not added: " + added.url);
            }
            const frame = document.createElement("iframe");
            frame.style.width = "1200px";
            frame.style.height = "900px";
            const loaded = new Promise((resolve) => (frame.onload = resolve));
            frame.src = "/rooms/checkout";
            document.body.appendChild(frame);
            await loaded;
            const doc = frame.contentDocument;
            const email = doc.querySelector("input[name='email']");
            if (!email) {
                const at = frame.contentWindow.location.href;
                throw new Error("no guest details form at " + at);
            }
            // let the interactions of the frame start
            await new Promise((resolve) => setTimeout(resolve, 1000));
            const form = email.form;
            form.querySelector("input[name='name']").value = "UI Booker";
            email.value = "ui.booker@example.com";
            form.querySelector("input[name='phone']").value = "+91 90000 00000";
            const rows = () => doc.querySelectorAll(
                ".o_hotel_guest_rows .o_hotel_guest_row"
            );
            const before = rows().length;
            doc.querySelector(".o_hotel_add_guest").click();
            await new Promise((resolve) => setTimeout(resolve, 200));
            if (rows().length !== before + 1) {
                throw new Error("add guest did not add a row");
            }
            const filled = [...rows()].slice(-2);
            filled[0].querySelector("input").value = "UI Partner";
            filled[1].querySelector("input").value = "UI Kid";
            filled[1].querySelector("select").value = "child";
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
            });
            if (!response.url.includes("/rooms/booking/requested")) {
                throw new Error("request not sent: " + response.url);
            }
            if (!(await response.text()).includes("UI Kid")) {
                throw new Error("guests missing on the confirmation page");
            }
            """,
        )
        reservation = self.env["hotel.reservation"].search(
            [("partner_id.email", "=", "ui.booker@example.com")]
        )
        self.assertTrue(reservation.is_website_booking)
        self.assertEqual(reservation.state, "draft")
        self.assertEqual(
            sorted(reservation.guest_ids.mapped("name")), ["UI Kid", "UI Partner"]
        )
        self.assertEqual((reservation.adults, reservation.children), (2, 1))
        self.assertEqual(
            reservation.guest_ids.partner_id.parent_id, reservation.partner_id
        )
