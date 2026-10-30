# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from urllib.parse import urlencode

from odoo import fields, http
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.http import request
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)

# The visitor's stay lives in the session until checkout instead of in a
# draft hotel.reservation, so abandoned website visits never show up in the
# front desk's reservation list.
CART_SESSION_KEY = "hotel_website_cart"
BOOKING_SESSION_KEY = "hotel_website_last_booking"
MAX_ACCOMPANYING_GUESTS = 20
MAX_ROOMS_PER_TYPE = 5
MAX_REVIEW_LENGTH = 2000
MAX_NOTE_LENGTH = 2000


class HotelWebsite(http.Controller):
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _notice_messages(self):
        """Visitor-facing text for the ``?notice=`` codes redirects carry."""
        return {
            "added": request.env._("Added to your stay."),
            "removed": request.env._("Removed from your stay."),
            "dates_changed": request.env._(
                "You picked different dates, so the rooms chosen for the previous "
                "dates were removed. Your new selection has been added."
            ),
            "unavailable": request.env._(
                "Sorry, not enough rooms of that type are free for these dates."
            ),
            "room_type_not_found": request.env._(
                "That room type cannot be booked online."
            ),
            "empty_cart": request.env._(
                "Your stay is empty. Choose your dates and a room first."
            ),
            "rooms_dropped": request.env._(
                "Your stay was updated because fewer rooms are free for your dates now."
            ),
        }

    def _cart_read(self):
        cart = request.session.get(CART_SESSION_KEY) or {}
        types = {}
        for type_id, qty in (cart.get("types") or {}).items():
            try:
                type_id, qty = int(type_id), int(qty)
            except (TypeError, ValueError):
                continue
            if qty > 0:
                types[type_id] = qty
        return {
            "checkin": cart.get("checkin") or "",
            "checkout": cart.get("checkout") or "",
            "types": types,
        }

    def _cart_write(self, checkin, checkout, types):
        request.session[CART_SESSION_KEY] = {
            "checkin": checkin,
            "checkout": checkout,
            # Session data is JSON: keys have to be strings.
            "types": {str(type_id): qty for type_id, qty in types.items()},
        }

    def _cart_clear(self):
        request.session.pop(CART_SESSION_KEY, None)

    def _bookable_type(self, room_type_id):
        room_types = request.env.website.hotel_room_types()
        try:
            room_type_id = int(room_type_id)
        except (TypeError, ValueError):
            return room_types.browse()
        return room_types.filtered(lambda rtype: rtype.id == room_type_id)

    def _stay_values(self, checkin_date, checkout_date, entries):
        website = request.env.website
        checkin_dt, checkout_dt = website._hotel_stay_datetimes(
            checkin_date, checkout_date
        )
        return {
            "checkin": fields.Date.to_string(checkin_date),
            "checkout": fields.Date.to_string(checkout_date),
            "checkin_label": website._hotel_date_label(checkin_date),
            "checkout_label": website._hotel_date_label(checkout_date),
            "checkin_time": website._hotel_hour_label(website.hotel_checkin_hour),
            "checkout_time": website._hotel_hour_label(website.hotel_checkout_hour),
            "checkin_dt": checkin_dt,
            "checkout_dt": checkout_dt,
            "entries": entries,
            "quote": website._hotel_quote(entries, checkin_dt, checkout_dt),
        }

    def _cart_stay(self):
        """The visitor's stay as it stands right now.

        A room type's quantity is trimmed to what is still free, and types
        no longer bookable are dropped, so every page works off a stay that
        can still be requested.

        :return: ``(stay, dropped)`` - ``stay`` is None when nothing is left;
            ``dropped`` tells the page to explain the change.
        """
        website = request.env.website
        cart = self._cart_read()
        if not cart["types"]:
            return None, False
        checkin_date, checkout_date, error = website._hotel_parse_stay(
            cart["checkin"], cart["checkout"]
        )
        if error:
            # Typically a stay whose arrival date has passed since.
            self._cart_clear()
            return None, True
        checkin_dt, checkout_dt = website._hotel_stay_datetimes(
            checkin_date, checkout_date
        )
        room_types = website.hotel_room_types()
        entries, kept, dropped = [], {}, False
        for room_type in room_types:
            wanted = cart["types"].get(room_type.id)
            if not wanted:
                continue
            free = len(website._hotel_free_rooms(room_type, checkin_dt, checkout_dt))
            allowed = min(wanted, free)
            dropped = dropped or allowed != wanted
            if allowed:
                kept[room_type.id] = allowed
                entries.append(
                    {
                        "room_type": room_type,
                        "qty": allowed,
                        "rooms": request.env["hotel.room"],
                    }
                )
        dropped = dropped or set(cart["types"]) - set(room_types.ids) != set()
        if not entries:
            self._cart_clear()
            return None, dropped
        if dropped:
            self._cart_write(cart["checkin"], cart["checkout"], kept)
        return self._stay_values(checkin_date, checkout_date, entries), dropped

    def _page_notice(self, notice, dropped):
        notices = self._notice_messages()
        return notices.get(notice) or (dropped and notices["rooms_dropped"]) or False

    def _stay_type_qty(self, stay, checkin, checkout):
        """Quantities already in the stay, when it is for these dates."""
        if not stay or (stay["checkin"], stay["checkout"]) != (checkin, checkout):
            return {}
        return {entry["room_type"].id: entry["qty"] for entry in stay["entries"]}

    # ------------------------------------------------------------------
    # Browsing
    # ------------------------------------------------------------------

    @http.route("/rooms", type="http", auth="public", website=True, sitemap=True)
    def rooms(self, checkin=None, checkout=None, room_type=None, notice=None, **kwargs):
        website = request.env.website
        stay, dropped = self._cart_stay()
        if not checkin and not checkout and stay:
            checkin, checkout = stay["checkin"], stay["checkout"]
        room_types = website.hotel_room_types()
        selected_type = room_types.filtered(
            lambda rtype: str(rtype.id) == str(room_type)
        )
        shown = selected_type or room_types
        values = {
            "room_types": room_types,
            "selected_type": selected_type,
            "cards": [website.hotel_room_type_card(rtype) for rtype in shown],
            "checkin": checkin or "",
            "checkout": checkout or "",
            "today": fields.Date.to_string(website._hotel_today()),
            "searched": False,
            "search_error": False,
            "nights": 0,
            "availability": {},
            "stay": stay,
            "stay_type_qty": {},
            "dates_differ": False,
            "max_per_type": MAX_ROOMS_PER_TYPE,
            "notice": self._page_notice(notice, dropped),
        }
        if checkin or checkout:
            checkin_date, checkout_date, error = website._hotel_parse_stay(
                checkin, checkout
            )
            values["search_error"] = error
            if not error:
                checkin_dt, checkout_dt = website._hotel_stay_datetimes(
                    checkin_date, checkout_date
                )
                values.update(
                    {
                        "searched": True,
                        "nights": website._hotel_stay_nights(checkin_dt, checkout_dt),
                        "checkin_label": website._hotel_date_label(checkin_date),
                        "checkout_label": website._hotel_date_label(checkout_date),
                        "availability": {
                            rtype.id: len(
                                website._hotel_free_rooms(
                                    rtype, checkin_dt, checkout_dt
                                )
                            )
                            for rtype in shown
                        },
                        "stay_type_qty": self._stay_type_qty(stay, checkin, checkout),
                        "dates_differ": bool(
                            stay
                            and (stay["checkin"], stay["checkout"])
                            != (checkin, checkout)
                        ),
                    }
                )
        return request.render("hotel_website.rooms_page", values)

    @http.route(
        "/rooms/<int:room_type_id>",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def room_type_detail(self, room_type_id, checkin=None, checkout=None, **kwargs):
        website = request.env.website
        room_type = self._bookable_type(room_type_id)
        if not room_type:
            raise request.not_found()
        stay, _dropped = self._cart_stay()
        if not checkin and not checkout and stay:
            checkin, checkout = stay["checkin"], stay["checkout"]
        card = website.hotel_room_type_card(room_type)
        free_count, search_error, nights = None, False, 0
        if checkin or checkout:
            checkin_date, checkout_date, search_error = website._hotel_parse_stay(
                checkin, checkout
            )
            if not search_error:
                checkin_dt, checkout_dt = website._hotel_stay_datetimes(
                    checkin_date, checkout_date
                )
                free_count = len(
                    website._hotel_free_rooms(room_type, checkin_dt, checkout_dt)
                )
                nights = website._hotel_stay_nights(checkin_dt, checkout_dt)
        reviews = room_type.sudo().room_review_ids.filtered("is_published")[:20]
        values = {
            "room_type": room_type,
            "card": card,
            "images": website._hotel_type_images(room_type, card["rooms"]),
            "reviews": reviews,
            "review_dates": {
                review.id: website._hotel_date_label(
                    website._hotel_local_datetime(review.create_date).date()
                )
                for review in reviews
            },
            "checkin": checkin or "",
            "checkout": checkout or "",
            "today": fields.Date.to_string(website._hotel_today()),
            "free_count": free_count,
            "search_error": search_error,
            "nights": nights,
            "in_stay_qty": self._stay_type_qty(stay, checkin, checkout).get(
                room_type.id, 0
            ),
            "stay": stay,
            "max_per_type": MAX_ROOMS_PER_TYPE,
            "is_public": request.env.user._is_public(),
        }
        return request.render("hotel_website.room_type_page", values)

    @http.route(
        "/hotel/gallery", type="http", auth="public", website=True, sitemap=True
    )
    def gallery(self, **kwargs):
        return request.render("hotel_website.gallery_page", {})

    # ------------------------------------------------------------------
    # Stay (cart)
    # ------------------------------------------------------------------

    @http.route(
        "/rooms/cart/add",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        sitemap=False,
    )
    def cart_add(
        self, room_type_id=None, qty=None, checkin=None, checkout=None, **kwargs
    ):
        website = request.env.website
        back = "/rooms?" + urlencode(
            {"checkin": checkin or "", "checkout": checkout or ""}
        )
        room_type = self._bookable_type(room_type_id)
        if not room_type:
            return request.redirect(back + "&notice=room_type_not_found")
        try:
            qty = max(1, min(int(qty or 1), MAX_ROOMS_PER_TYPE))
        except (TypeError, ValueError):
            qty = 1
        checkin_date, checkout_date, error = website._hotel_parse_stay(
            checkin, checkout
        )
        if error:
            # The rooms page re-validates the same dates and shows the error.
            return request.redirect(back)
        checkin_dt, checkout_dt = website._hotel_stay_datetimes(
            checkin_date, checkout_date
        )
        if len(website._hotel_free_rooms(room_type, checkin_dt, checkout_dt)) < qty:
            return request.redirect(back + "&notice=unavailable")

        cart = self._cart_read()
        dates = (
            fields.Date.to_string(checkin_date),
            fields.Date.to_string(checkout_date),
        )
        types, notice = cart["types"], "added"
        if (cart["checkin"], cart["checkout"]) != dates:
            # One reservation has one arrival and one departure.
            if types:
                notice = "dates_changed"
            types = {}
        types[room_type.id] = qty
        self._cart_write(*dates, types)
        return request.redirect("/rooms/cart?" + urlencode({"notice": notice}))

    @http.route(
        "/rooms/cart/remove",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        sitemap=False,
    )
    def cart_remove(self, room_type_id=None, **kwargs):
        cart = self._cart_read()
        try:
            room_type_id = int(room_type_id)
        except (TypeError, ValueError):
            # not a room type of the stay: nothing to remove
            return request.redirect("/rooms/cart")
        cart["types"].pop(room_type_id, None)
        if cart["types"]:
            self._cart_write(cart["checkin"], cart["checkout"], cart["types"])
        else:
            self._cart_clear()
        return request.redirect("/rooms/cart?notice=removed")

    @http.route("/rooms/cart", type="http", auth="public", website=True, sitemap=False)
    def cart(self, notice=None, **kwargs):
        stay, dropped = self._cart_stay()
        return request.render(
            "hotel_website.cart_page",
            {"stay": stay, "notice": self._page_notice(notice, dropped)},
        )

    # ------------------------------------------------------------------
    # Checkout
    # ------------------------------------------------------------------

    def _read_contact_details(self, post, is_public):
        """Validated main-guest details from the checkout form.

        :return: ``(details, errors)``
        """
        errors = {}
        details = {"notes": (post.get("notes") or "").strip()[:MAX_NOTE_LENGTH]}
        if not is_public:
            # Booking under an account: the account's contact is the guest.
            # It is never overwritten from a public form.
            details["partner"] = request.env.user.partner_id
            return details, errors
        name = (post.get("name") or "").strip()
        email = email_normalize(post.get("email") or "")
        phone = (post.get("phone") or "").strip()
        if not name:
            errors["name"] = request.env._("Please enter your name.")
        if not email:
            errors["email"] = request.env._("Please enter a valid email address.")
        if not phone:
            errors["phone"] = request.env._(
                "Please enter a phone number so the hotel can reach you."
            )
        try:
            country = (
                request.env["res.country"].sudo().browse(int(post.get("country_id")))
            )
            country = country.exists()
        except (TypeError, ValueError):
            country = request.env["res.country"]
        details.update(
            {
                "name": name[:128],
                "email": email,
                "phone": phone[:64],
                "street": (post.get("street") or "").strip()[:128],
                "city": (post.get("city") or "").strip()[:64],
                "zip": (post.get("zip") or "").strip()[:24],
                "country_id": country.id,
            }
        )
        return details, errors

    def _read_accompanying_guests(self):
        form = request.httprequest.form
        guests = []
        for name, guest_type in zip(
            form.getlist("guest_name"), form.getlist("guest_type"), strict=False
        ):
            name = (name or "").strip()
            if name:
                guests.append(
                    {
                        "name": name[:128],
                        "guest_type": "child" if guest_type == "child" else "adult",
                    }
                )
        return guests

    def _book_stay(self, stay, details, guests):
        """Record the stay as a reservation request.

        The reservation is left in draft with one line per requested room,
        each carrying only its room type. The front desk confirms it with
        the usual Confirm button, which assigns free rooms of those types
        (hotel.reservation._assign_website_rooms) and then runs
        hotel_reservation's own confirmation."""
        website = request.env.website
        company = website.company_id

        partner = details.get("partner") or request.env["res.partner"].sudo().create(
            {
                "name": details["name"],
                "email": details["email"],
                "phone": details["phone"],
                "street": details["street"] or False,
                "city": details["city"] or False,
                "zip": details["zip"] or False,
                "country_id": details["country_id"] or False,
                "lang": request.lang.code,
                "company_id": company.id,
            }
        )
        partner = partner.sudo().with_company(company)
        pricelist = partner.property_product_pricelist or request.env[
            "product.pricelist"
        ].sudo().search([("company_id", "in", [False, company.id])], limit=1)
        if not pricelist:
            raise UserError(
                request.env._(
                    "Online booking is unavailable right now. Please contact the hotel."
                )
            )

        # Last look before recording the request: rooms may have been booked
        # since the visitor opened the guest details page.
        for entry in stay["entries"]:
            free = website._hotel_free_rooms(
                entry["room_type"], stay["checkin_dt"], stay["checkout_dt"]
            )
            if len(free) < entry["qty"]:
                raise UserError(
                    request.env._(
                        "Only %(count)s %(room_type)s room(s) are still free for your "
                        "dates. Please go back to your stay and adjust it.",
                        count=len(free),
                        room_type=entry["room_type"].name,
                    )
                )

        addresses = partner.address_get(["invoice", "delivery", "contact"])
        reservation = (
            request.env["hotel.reservation"]
            .sudo()
            .with_company(company)
            .create(
                {
                    "company_id": company.id,
                    "is_website_booking": True,
                    "partner_id": partner.id,
                    "partner_invoice_id": addresses["invoice"],
                    "partner_shipping_id": addresses["delivery"],
                    "partner_order_id": addresses["contact"],
                    "pricelist_id": pricelist.id,
                    "checkin": stay["checkin_dt"],
                    "checkout": stay["checkout_dt"],
                    "reservation_line": [
                        Command.create(
                            {
                                "categ_id": entry["room_type"].id,
                                "name": entry["room_type"].name,
                            }
                        )
                        for entry in stay["entries"]
                        for _index in range(entry["qty"])
                    ],
                    "guest_ids": [Command.create(guest) for guest in guests],
                }
            )
        )
        if details["notes"]:
            reservation.message_post(
                body=request.env._(
                    "Note from the guest (website request): %s", details["notes"]
                ),
                subtype_xmlid="mail.mt_note",
            )
        if reservation.partner_id.email:
            reservation.message_post(
                body=request.env._(
                    "Thank you for your reservation request %(number)s at %(hotel)s, "
                    "from %(checkin)s to %(checkout)s. Our reservations team will "
                    "confirm your room shortly.",
                    number=reservation.reservation_no,
                    hotel=company.name,
                    checkin=stay["checkin_label"],
                    checkout=stay["checkout_label"],
                ),
                partner_ids=reservation.partner_id.ids,
                author_id=company.partner_id.id,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )
        return reservation

    @http.route(
        "/rooms/checkout",
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
        sitemap=False,
    )
    def checkout(self, **post):
        stay, dropped = self._cart_stay()
        if not stay:
            notice = "rooms_dropped" if dropped else "empty_cart"
            return request.redirect(f"/rooms/cart?notice={notice}")
        is_post = request.httprequest.method == "POST"
        if is_post and dropped:
            # The stay changed under the visitor; let them see it before
            # sending something different from what they reviewed.
            return request.redirect("/rooms/cart?notice=rooms_dropped")

        is_public = request.env.user._is_public()
        errors, guests = {}, []
        if is_post:
            details, errors = self._read_contact_details(post, is_public)
            guests = self._read_accompanying_guests()
            total_guests = 1 + len(guests)
            if len(guests) > MAX_ACCOMPANYING_GUESTS:
                errors["guests"] = request.env._(
                    "Online requests can list up to %(count)s accompanying guests. "
                    "Please contact us for a larger group.",
                    count=MAX_ACCOMPANYING_GUESTS,
                )
            elif total_guests > stay["quote"]["capacity"]:
                errors["guests"] = request.env._(
                    "%(guests)s guests do not fit in the selected rooms, which sleep "
                    "%(capacity)s. Add another room or remove guests.",
                    guests=total_guests,
                    capacity=stay["quote"]["capacity"],
                )
            if not errors:
                try:
                    with request.env.cr.savepoint():
                        reservation = self._book_stay(stay, details, guests)
                except (UserError, ValidationError) as exc:
                    request.env.invalidate_all()
                    errors["booking"] = exc.args[0] if exc.args else str(exc)
                    _logger.info(
                        "Website reservation request refused: %s", errors["booking"]
                    )
                else:
                    self._cart_clear()
                    request.session[BOOKING_SESSION_KEY] = reservation.id
                    return request.redirect("/rooms/booking/requested")

        values = {
            "stay": stay,
            "form": post,
            "errors": errors,
            "is_public": is_public,
            "partner": request.env.user.partner_id,
            "countries": request.env["res.country"].sudo().search([]),
            "guest_rows": guests + [{}],
        }
        return request.render("hotel_website.checkout_page", values)

    @http.route(
        "/rooms/booking/requested",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def booking_requested(self, **kwargs):
        reservation_id = request.session.get(BOOKING_SESSION_KEY)
        reservation = request.env["hotel.reservation"].sudo()
        if reservation_id:
            reservation = reservation.browse(int(reservation_id)).exists()
        if not reservation:
            return request.redirect("/rooms")
        return request.render(
            "hotel_website.booking_requested_page",
            {
                "reservation": reservation,
                "summary": request.env.website._hotel_reservation_summary(reservation),
                "is_public": request.env.user._is_public(),
            },
        )

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------

    @http.route(
        "/rooms/<int:room_type_id>/review",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        sitemap=False,
    )
    def room_type_review(self, room_type_id, rating=None, comment=None, **kwargs):
        room_type = self._bookable_type(room_type_id)
        if not room_type:
            raise request.not_found()
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            rating = 0
        if 1 <= rating <= 5:
            partner = request.env.user.partner_id
            request.env["room.review"].sudo().create(
                {
                    "room_type_id": room_type.id,
                    "partner_id": partner.id,
                    "name": partner.name,
                    "rating": rating,
                    "comment": (comment or "").strip()[:MAX_REVIEW_LENGTH],
                }
            )
        return request.redirect(f"/rooms/{room_type.id}#reviews")
