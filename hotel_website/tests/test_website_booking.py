# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tests import HttpCase, new_test_user, tagged

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

    def test_logged_in_guest_can_review_a_room_type(self):
        reviewer = new_test_user(
            self.env, login="hotel_reviewer", groups="base.group_portal"
        )
        self.authenticate("hotel_reviewer", "hotel_reviewer")
        token = self._csrf(f"/rooms/{self.suite.id}")
        self._open(
            f"/rooms/{self.suite.id}/review",
            data={"csrf_token": token, "rating": "4", "comment": "Quiet and clean"},
        )
        review = self.env["room.review"].search([("room_type_id", "=", self.suite.id)])
        self.assertEqual((review.rating, review.partner_id), (4, reviewer.partner_id))
        self.assertIn("Quiet and clean", self._open(f"/rooms/{self.suite.id}").text)
