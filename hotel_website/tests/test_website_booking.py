# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import re
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tests import HttpCase, new_test_user, tagged
from odoo.tools import BinaryBytes

from odoo.addons.google_recaptcha.models.ir_http import IrHttp

CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')
TITLE_RE = re.compile(r"<title>([^<]*)</title>")


@tagged("post_install", "-at_install")
class TestHotelWebsiteBooking(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("base.default_website")
        cls.suite = cls.env["hotel.room.type"].create({"name": "WebTest Suite"})
        cls.deluxe = cls.env["hotel.room.type"].create({"name": "WebTest Deluxe"})
        room_obj = cls.env["hotel.room"]
        cls.suite_a = room_obj.create(
            {
                "name": "WT-A1",
                "room_categ_id": cls.suite.id,
                "capacity": 2,
                "list_price": 120.0,
            }
        )
        cls.suite_b = room_obj.create(
            {
                "name": "WT-A2",
                "room_categ_id": cls.suite.id,
                "capacity": 2,
                "list_price": 150.0,
            }
        )
        cls.deluxe_a = room_obj.create(
            {
                "name": "WT-B1",
                "room_categ_id": cls.deluxe.id,
                "capacity": 3,
                "list_price": 200.0,
            }
        )
        if not cls.env["product.pricelist"].search([], limit=1):
            cls.env["product.pricelist"].create({"name": "WebTest Pricelist"})
        cls.checkin = cls.website._hotel_today() + timedelta(days=40)
        cls.checkout = cls.checkin + timedelta(days=2)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _open(self, url, data=None):
        self.env.flush_all()
        response = self.url_open(url, data=data)
        self.env.invalidate_all()
        return response

    def _dates(self):
        return fields.Date.to_string(self.checkin), fields.Date.to_string(self.checkout)

    def _csrf(self, url):
        response = self._open(url)
        self.assertEqual(response.status_code, 200, url)
        match = CSRF_RE.search(response.text)
        self.assertTrue(match, f"{url} should carry a CSRF token")
        return match.group(1)

    def _add_to_cart(self, room_type, qty=1):
        checkin, checkout = self._dates()
        token = self._csrf(f"/rooms?checkin={checkin}&checkout={checkout}")
        return self._open(
            "/rooms/cart/add",
            data={
                "csrf_token": token,
                "room_type_id": room_type.id,
                "qty": qty,
                "checkin": checkin,
                "checkout": checkout,
            },
        )

    def _checkout(self, **overrides):
        data = {
            "csrf_token": self._csrf("/rooms/checkout"),
            "name": "Web Guest",
            "email": "web.guest@example.com",
            "phone": "+91 99999 00000",
        }
        data.update(overrides)
        return self._open("/rooms/checkout", data=data)

    def _request(self, email="web.guest@example.com", **overrides):
        return self.env["hotel.reservation"].search([("partner_id.email", "=", email)])

    def _book_at_desk(self, room, partner=None):
        """A reservation made the usual way, at the front desk."""
        checkin_dt, checkout_dt = self.website._hotel_stay_datetimes(
            self.checkin, self.checkout
        )
        partner = partner or self.env["res.partner"].create({"name": "Desk Guest"})
        reservation = self.env["hotel.reservation"].create(
            {
                "partner_id": partner.id,
                "pricelist_id": self.env["product.pricelist"].search([], limit=1).id,
                "partner_invoice_id": partner.id,
                "partner_order_id": partner.id,
                "partner_shipping_id": partner.id,
                "checkin": checkin_dt,
                "checkout": checkout_dt,
                "reservation_line": [
                    Command.create(
                        {
                            "categ_id": room.room_categ_id.id,
                            "reserve": [Command.set(room.ids)],
                        }
                    )
                ],
            }
        )
        reservation.confirmed_reservation()
        return reservation

    # ------------------------------------------------------------------
    # browsing
    # ------------------------------------------------------------------

    def test_pages_render(self):
        for url in [
            "/",
            "/rooms",
            f"/rooms/{self.suite.id}",
            "/rooms/cart",
            "/hotel/gallery",
        ]:
            self.assertEqual(self._open(url).status_code, 200, url)

    def test_website_shows_room_types_not_rooms(self):
        checkin, checkout = self._dates()
        text = self._open(f"/rooms?checkin={checkin}&checkout={checkout}").text
        self.assertIn("WebTest Suite", text)
        self.assertIn("WebTest Deluxe", text)
        self.assertNotIn("WT-A1", text)
        self.assertNotIn("WT-B1", text)

    def test_availability_is_counted_per_room_type(self):
        checkin, checkout = self._dates()
        url = f"/rooms/{self.suite.id}?checkin={checkin}&checkout={checkout}"
        self._book_at_desk(self.suite_a)
        self.assertIn("Last room available", self._open(url).text)
        self._book_at_desk(self.suite_b)
        text = self._open(url).text
        self.assertIn("Not available for these dates", text)
        self.assertNotIn(f'name="room_type_id" value="{self.suite.id}"', text)

    def test_hotel_name_is_the_company_name(self):
        self.website.company_id.name = "WebTest Grand Hotel"
        home = self._open("/").text
        self.assertIn("WebTest Grand Hotel", home)
        self.assertTrue(TITLE_RE.search(home).group(1).endswith("WebTest Grand Hotel"))
        rooms_title = TITLE_RE.search(self._open("/rooms").text).group(1)
        self.assertEqual(rooms_title, "Rooms & Suites | WebTest Grand Hotel")

    def test_unbookable_room_types_are_hidden(self):
        self.deluxe_a.website_booking_published = False
        self.assertEqual(self._open(f"/rooms/{self.deluxe.id}").status_code, 404)
        self.assertNotIn("WebTest Deluxe", self._open("/rooms").text)

    # ------------------------------------------------------------------
    # requests
    # ------------------------------------------------------------------

    def test_online_request_is_left_for_the_front_desk(self):
        self._add_to_cart(self.suite)
        response = self._checkout(
            guest_name=["Riya Guest"], guest_type=["adult"], notes="Arriving late"
        )
        self.assertIn("/rooms/booking/requested", response.url)

        reservation = self._request()
        self.assertEqual(len(reservation), 1)
        self.assertIn(reservation.reservation_no, response.text)
        self.assertEqual(reservation.state, "draft")
        self.assertTrue(reservation.is_website_booking)
        self.assertEqual(reservation.reservation_line.categ_id, self.suite)
        self.assertFalse(
            reservation.reservation_line.reserve, "no room is picked online"
        )
        self.assertFalse(
            self.env["hotel.room.reservation.line"].search(
                [("reservation_id", "=", reservation.id)]
            ),
            "a request must not block any room",
        )
        self.assertEqual(reservation.guest_ids.parent_id, reservation.partner_id)
        self.assertIn("Arriving late", "".join(reservation.message_ids.mapped("body")))

    def test_one_reservation_line_per_requested_room(self):
        self._add_to_cart(self.suite, qty=2)
        self._add_to_cart(self.deluxe, qty=1)
        self.assertIn("/rooms/booking/requested", self._checkout().url)
        lines = self._request().reservation_line
        self.assertEqual(len(lines), 3)
        self.assertEqual(
            sorted(lines.categ_id.mapped("name")), ["WebTest Deluxe", "WebTest Suite"]
        )
        self.assertEqual(
            len(lines.filtered(lambda line: line.categ_id == self.suite)), 2
        )

    def test_confirming_a_request_assigns_a_free_room(self):
        self._add_to_cart(self.suite)
        self._checkout()
        reservation = self._request()
        # The cheapest suite gets booked at the desk before the request is handled.
        self._book_at_desk(self.suite_a)

        reservation.confirmed_reservation()

        self.assertEqual(reservation.state, "confirm")
        self.assertEqual(reservation.reservation_line.reserve, self.suite_b)
        self.assertTrue(
            self.env["hotel.room.reservation.line"].search(
                [
                    ("reservation_id", "=", reservation.id),
                    ("room_id", "=", self.suite_b.id),
                ]
            )
        )
        reservation.create_folio()
        self.assertEqual(reservation.state, "done")

    def test_confirming_fails_when_the_type_is_sold_out(self):
        self._add_to_cart(self.suite)
        self._checkout()
        reservation = self._request()
        self._book_at_desk(self.suite_a)
        self._book_at_desk(self.suite_b)
        with self.assertRaises(UserError):
            reservation.confirmed_reservation()

    def test_request_cannot_exceed_the_free_rooms(self):
        response = self._add_to_cart(self.suite, qty=3)
        self.assertIn("notice=unavailable", response.url)
        self.assertIn("You have not chosen a room yet", self._open("/rooms/cart").text)

    def test_capacity_counts_the_smallest_room_of_the_type(self):
        self._add_to_cart(self.suite)
        response = self._checkout(
            email="too.many@example.com",
            guest_name=["Guest One", "Guest Two"],
            guest_type=["adult", "child"],
        )
        self.assertIn("do not fit in the selected rooms", response.text)
        self.assertFalse(
            self.env["res.partner"].search([("email", "=", "too.many@example.com")])
        )

    def test_rooms_booked_meanwhile_are_not_requested(self):
        self._add_to_cart(self.suite, qty=2)
        token = self._csrf("/rooms/checkout")
        self._book_at_desk(self.suite_a)
        response = self._open(
            "/rooms/checkout",
            data={
                "csrf_token": token,
                "name": "Late Guest",
                "email": "late.guest@example.com",
                "phone": "+91 88888 00000",
            },
        )
        self.assertIn("/rooms/cart", response.url)
        self.assertIn("fewer rooms are free", response.text)
        self.assertFalse(self._request("late.guest@example.com"))

    def test_past_dates_are_rejected(self):
        yesterday = fields.Date.to_string(
            self.website._hotel_today() - timedelta(days=1)
        )
        _checkin, checkout = self._dates()
        response = self._open(f"/rooms?checkin={yesterday}&checkout={checkout}")
        self.assertIn("cannot be in the past", response.text)

    def test_desk_reservations_keep_the_oca_room_check(self):
        partner = self.env["res.partner"].create({"name": "Desk Only"})
        checkin_dt, checkout_dt = self.website._hotel_stay_datetimes(
            self.checkin, self.checkout
        )
        with self.assertRaises(ValidationError):
            self.env["hotel.reservation"].create(
                {
                    "partner_id": partner.id,
                    "pricelist_id": self.env["product.pricelist"]
                    .search([], limit=1)
                    .id,
                    "partner_invoice_id": partner.id,
                    "partner_order_id": partner.id,
                    "partner_shipping_id": partner.id,
                    "checkin": checkin_dt,
                    "checkout": checkout_dt,
                    "reservation_line": [Command.create({"categ_id": self.suite.id})],
                }
            )

    # ------------------------------------------------------------------
    # portal, reviews
    # ------------------------------------------------------------------

    def test_portal_shows_the_pending_request_to_its_owner_only(self):
        owner = new_test_user(
            self.env, login="hotel_portal_owner", groups="base.group_portal"
        )
        new_test_user(self.env, login="hotel_portal_other", groups="base.group_portal")

        self.authenticate("hotel_portal_owner", "hotel_portal_owner")
        self._add_to_cart(self.suite)
        self.assertIn(
            "/rooms/booking/requested",
            self._open(
                "/rooms/checkout", data={"csrf_token": self._csrf("/rooms/checkout")}
            ).url,
        )
        reservation = self.env["hotel.reservation"].search(
            [("partner_id", "=", owner.partner_id.id)]
        )
        listing = self._open("/my/reservations").text
        self.assertIn(reservation.reservation_no, listing)
        self.assertIn("Awaiting confirmation", listing)

        self.authenticate("hotel_portal_other", "hotel_portal_other")
        self.assertNotIn(
            reservation.reservation_no,
            self._open(f"/my/reservations/{reservation.id}").text,
        )

    def _review(self, room_type, rating="4", comment="Quiet and clean"):
        token = self._csrf(f"/rooms/{room_type.id}")
        return self._open(
            f"/rooms/{room_type.id}/review",
            data={"csrf_token": token, "rating": rating, "comment": comment},
        )

    def test_guest_who_stayed_can_review_once_after_moderation(self):
        reviewer = new_test_user(
            self.env, login="hotel_reviewer", groups="base.group_portal"
        )
        self._book_at_desk(self.suite_a, partner=reviewer.partner_id)
        self.authenticate("hotel_reviewer", "hotel_reviewer")
        self.assertIn(
            "Share your experience", self._open(f"/rooms/{self.suite.id}").text
        )
        response = self._review(self.suite)
        self.assertIn("once the hotel has published it", response.text)
        review = self.env["room.review"].search([("room_type_id", "=", self.suite.id)])
        self.assertEqual((review.rating, review.partner_id), (4, reviewer.partner_id))
        # waits for the hotel
        self.assertFalse(review.is_published)
        self.assertNotIn("Quiet and clean", self._open(f"/rooms/{self.suite.id}").text)
        # one review per guest and room type
        self._review(self.suite, comment="Second try")
        self.assertEqual(
            self.env["room.review"].search_count(
                [("room_type_id", "=", self.suite.id)]
            ),
            1,
        )
        self.assertIn("already reviewed", self._open(f"/rooms/{self.suite.id}").text)
        review.is_published = True
        self.assertIn("Quiet and clean", self._open(f"/rooms/{self.suite.id}").text)

    def test_only_guests_who_stayed_can_review(self):
        new_test_user(self.env, login="hotel_no_stay", groups="base.group_portal")
        self.authenticate("hotel_no_stay", "hotel_no_stay")
        page = self._open(f"/rooms/{self.suite.id}").text
        self.assertNotIn("Share your experience", page)
        self.assertIn("guests who stayed in this room type", page)
        self._review(self.suite)
        self.assertFalse(
            self.env["room.review"].search([("room_type_id", "=", self.suite.id)])
        )

    # ------------------------------------------------------------------
    # abuse of the public request form
    # ------------------------------------------------------------------

    def test_request_checks_the_captcha(self):
        def refuse(self_, action):
            self.assertEqual(action, "hotel_website_booking")
            raise UserError(self_.env._("Suspicious activity detected"))

        self._add_to_cart(self.suite)
        with patch.object(IrHttp, "_verify_request_recaptcha_token", refuse):
            response = self._checkout(email="bot@example.com")
        self.assertIn("Suspicious activity detected", response.text)
        self.assertFalse(self._request("bot@example.com"))
        self.assertIn(
            'data-captcha="hotel_website_booking"', self._open("/rooms/checkout").text
        )

    def _website_request(self, email, **vals):
        partner = self.env["res.partner"].create({"name": email, "email": email})
        checkin_dt, checkout_dt = self.website._hotel_stay_datetimes(
            self.checkin, self.checkout
        )
        values = {
            "is_website_booking": True,
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_order_id": partner.id,
            "partner_shipping_id": partner.id,
            "pricelist_id": self.env["product.pricelist"].search([], limit=1).id,
            "checkin": checkin_dt,
            "checkout": checkout_dt,
            "reservation_line": [Command.create({"categ_id": self.suite.id})],
        }
        values.update(vals)
        return self.env["hotel.reservation"].create(values)

    def test_requests_per_email_are_limited(self):
        for _index in range(3):
            self._website_request("busy.guest@example.com")
        self._add_to_cart(self.suite)
        response = self._checkout(email="busy.guest@example.com")
        self.assertIn("already sent several reservation requests", response.text)
        self.assertEqual(len(self._request("busy.guest@example.com")), 3)

    def test_requests_per_ip_address_are_limited(self):
        for index in range(5):
            self._website_request(
                f"guest{index}@example.com", website_request_ip="127.0.0.1"
            )
        self._add_to_cart(self.suite)
        response = self._checkout(email="sixth.guest@example.com")
        self.assertIn("already sent several reservation requests", response.text)
        self.assertFalse(self._request("sixth.guest@example.com"))

    # ------------------------------------------------------------------
    # requests do not wait forever
    # ------------------------------------------------------------------

    def test_unconfirmed_requests_expire(self):
        self.env["ir.config_parameter"].sudo().set_int(
            "hotel_website.request_expiry_days", 3
        )
        old = self._website_request("old.request@example.com")
        recent = self._website_request("recent.request@example.com")
        confirmed = self._website_request("confirmed.request@example.com")
        confirmed.confirmed_reservation()
        self.env.cr.execute(
            "UPDATE hotel_reservation SET create_date = %s WHERE id IN %s",
            [
                fields.Datetime.now() - timedelta(days=4),
                tuple((old | confirmed).ids),
            ],
        )
        self.env.invalidate_all()
        expired = self.env["hotel.reservation"]._cron_expire_website_requests()
        self.assertEqual(expired, old)
        self.assertEqual(
            (old.state, recent.state, confirmed.state), ("cancel", "draft", "confirm")
        )
        self.assertIn("could not confirm", old.message_ids[:1].body)

    def test_request_pages_say_no_room_is_held(self):
        self._add_to_cart(self.suite)
        self.assertIn("no room is held", self._open("/rooms/checkout").text)
        response = self._checkout()
        self.assertIn("No room is held for you until we confirm it", response.text)

    # ------------------------------------------------------------------
    # website layout, images, sitemap
    # ------------------------------------------------------------------

    def test_layout_only_on_hotel_websites(self):
        self.website.company_id.name = "WebTest Grand Hotel"
        self.website.name = "WebTest Shop"
        self.website.hotel_layout = False
        home = self._open("/").text
        self.assertTrue(TITLE_RE.search(home).group(1).endswith("WebTest Shop"))
        self.assertNotIn("o_hotel_hero", home)
        # the booking pages still work there
        self.assertEqual(self._open("/rooms").status_code, 200)

    def test_no_fonts_of_its_own(self):
        """The pages use the website theme's fonts: the module loads none
        (the theme's own font settings stay the website's business)."""
        for url in ["/", "/rooms", f"/rooms/{self.suite.id}"]:
            page = self._open(url).text
            self.assertNotIn("Cormorant", page, url)
            self.assertNotIn("family=Jost", page, url)

    def test_photos_are_cacheable_urls(self):
        # a 1x1 PNG
        self.suite.image_1920 = BinaryBytes(
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8Dw"
                "HwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
            )
        )
        page = self._open(f"/rooms/{self.suite.id}").text
        self.assertNotIn("data:image", page)
        url = re.search(
            rf"/web/image/hotel.room.type/{self.suite.id}/image_1024[^\"']*", page
        )
        self.assertTrue(url, "the room type photo should be a /web/image URL")
        # visitors can load it, although they cannot read room types
        response = self._open(url.group(0).replace("&amp;", "&"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.suite.image_1024.content)
        # not the photo of a room type the website does not offer
        (self.suite_a | self.suite_b).website_booking_published = False
        self.assertNotEqual(
            self._open(url.group(0).replace("&amp;", "&")).content,
            self.suite.image_1024.content,
        )

    def test_room_type_pages_in_sitemap(self):
        sitemap = self._open("/sitemap.xml").text
        self.assertIn(f"/rooms/{self.suite.id}<", sitemap)
