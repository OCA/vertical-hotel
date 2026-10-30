# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import format_date, html2plaintext
from odoo.tools.image import image_data_uri

# Longest stay accepted in one online booking. Longer stays are unusual
# enough that the front desk should arrange them.
MAX_WEBSITE_NIGHTS = 60
ROOM_TYPE_FALLBACK_IMAGE = "/hotel_website/static/src/image/room-detail1.png"


class Website(models.Model):
    _inherit = "website"

    hotel_checkin_hour = fields.Float(
        "Hotel Check-in Time",
        default=14.0,
        help="Arrival time given to rooms booked on this website.",
    )
    hotel_checkout_hour = fields.Float(
        "Hotel Check-out Time",
        default=11.0,
        help="Departure time given to rooms booked on this website.",
    )

    @api.constrains("hotel_checkin_hour", "hotel_checkout_hour")
    def _check_hotel_hours(self):
        for website in self:
            for hour in (website.hotel_checkin_hour, website.hotel_checkout_hour):
                if not 0 <= hour < 24:
                    raise ValidationError(
                        self.env._(
                            "Check-in and check-out times must be between "
                            "00:00 and 23:59."
                        )
                    )

    # ------------------------------------------------------------------
    # Dates
    # ------------------------------------------------------------------

    def _hotel_tz(self):
        """Wall-clock timezone of the hotel.

        Guests pick calendar dates; they have to land on the same day the
        receptionist sees in the back office, whatever timezone the visitor
        browses from."""
        self.ensure_one()
        admin = self.env.ref("base.user_admin", raise_if_not_found=False)
        # sudo: website visitors cannot read the company's contact record.
        tz_name = (
            self.sudo().company_id.partner_id.tz or (admin and admin.sudo().tz) or "UTC"
        )
        return ZoneInfo(tz_name)

    def _hotel_today(self):
        self.ensure_one()
        return datetime.now(self._hotel_tz()).date()

    def _hotel_parse_stay(self, checkin, checkout):
        """Validate the two dates of a stay.

        :return: ``(checkin_date, checkout_date, error)`` where ``error`` is
            a message for the visitor, or ``False`` when the dates are usable.
        """
        self.ensure_one()
        if not checkin or not checkout:
            return (
                False,
                False,
                self.env._("Please choose your arrival and departure dates."),
            )
        try:
            checkin_date = fields.Date.to_date(checkin)
            checkout_date = fields.Date.to_date(checkout)
        except (TypeError, ValueError):
            return False, False, self.env._("Those dates are not valid.")
        if checkin_date < self._hotel_today():
            return False, False, self.env._("The arrival date cannot be in the past.")
        if checkout_date <= checkin_date:
            return (
                False,
                False,
                self.env._("Departure must be at least one day after arrival."),
            )
        if (checkout_date - checkin_date).days > MAX_WEBSITE_NIGHTS:
            return (
                False,
                False,
                self.env._(
                    "Online bookings are limited to %(nights)s nights. "
                    "Please contact us for a longer stay.",
                    nights=MAX_WEBSITE_NIGHTS,
                ),
            )
        return checkin_date, checkout_date, False

    def _hotel_stay_datetimes(self, checkin_date, checkout_date):
        """Turn stay dates into the UTC datetimes hotel.reservation stores,
        using this website's check-in and check-out times."""
        self.ensure_one()
        tz = self._hotel_tz()

        def to_utc(day, hour):
            local = (datetime.combine(day, time()) + timedelta(hours=hour)).replace(
                tzinfo=tz
            )
            return local.astimezone(UTC).replace(tzinfo=None)

        return (
            to_utc(checkin_date, self.hotel_checkin_hour),
            to_utc(checkout_date, self.hotel_checkout_hour),
        )

    def _hotel_local_datetime(self, value):
        self.ensure_one()
        return value.replace(tzinfo=UTC).astimezone(self._hotel_tz())

    def _hotel_date_label(self, value):
        return format_date(self.env, value, date_format="medium")

    @api.model
    def _hotel_hour_label(self, hour):
        hours, minutes = divmod(round(hour * 60), 60)
        return f"{hours:02d}:{minutes:02d}"

    # ------------------------------------------------------------------
    # Room types
    # ------------------------------------------------------------------

    def _hotel_bookable_room_domain(self):
        self.ensure_one()
        return [
            ("website_booking_published", "=", True),
            ("company_id", "in", [False, self.company_id.id]),
        ]

    def hotel_room_types(self):
        """Room types with at least one room bookable on this website."""
        self.ensure_one()
        rooms = self.env["hotel.room"].sudo().search(self._hotel_bookable_room_domain())
        return rooms.room_categ_id.sorted(
            lambda rtype: (rtype.website_sequence, rtype.name or "")
        )

    def _hotel_type_rooms(self, room_type):
        self.ensure_one()
        return self.env["hotel.room"]._hotel_website_rooms(room_type, self.company_id)

    def hotel_room_type_card(self, room_type):
        """What the website shows about a room type, drawn from its rooms."""
        self.ensure_one()
        room_type = room_type.sudo()
        rooms = self._hotel_type_rooms(room_type)
        return {
            "room_type": room_type,
            "rooms": rooms,
            "image": self._hotel_type_images(room_type, rooms, limit=1)[0],
            "capacity": min(rooms.mapped("capacity"), default=0),
            "max_capacity": max(rooms.mapped("capacity"), default=0),
            "price_from": min(rooms.mapped("list_price"), default=0.0),
            "amenities": rooms.room_amenities_ids,
            "max_adult": max(rooms.mapped("max_adult"), default=0),
            "max_child": max(rooms.mapped("max_child"), default=0),
            "excerpt": self._hotel_excerpt(room_type.website_description),
        }

    @api.model
    def _hotel_type_images(self, room_type, rooms, limit=6):
        images = []
        if room_type.image_1024:
            images.append(image_data_uri(room_type.image_1024))
        images += [image_data_uri(room.image_1024) for room in rooms if room.image_1024]
        # Rooms of one type often share a photo; show each picture once.
        images = list(dict.fromkeys(images))[:limit]
        return images or [ROOM_TYPE_FALLBACK_IMAGE]

    @api.model
    def _hotel_excerpt(self, html, length=180):
        text = " ".join(html2plaintext(html or "").split())
        if len(text) <= length:
            return text
        return text[:length].rsplit(" ", 1)[0] + "\u2026"

    def _hotel_free_rooms(self, room_type, checkin_dt, checkout_dt):
        self.ensure_one()
        return self.env["hotel.room"]._hotel_website_free_rooms(
            room_type, checkin_dt, checkout_dt, self.company_id
        )

    # ------------------------------------------------------------------
    # Pricing
    # ------------------------------------------------------------------

    def _hotel_stay_nights(self, checkin_dt, checkout_dt):
        """Billable days, counted by hotel_reservation's own rule so the
        estimate matches the quantity create_folio() will put on the folio
        (which honours the company's additional hours setting)."""
        self.ensure_one()
        reservation = (
            self.env["hotel.reservation"].sudo().new({"company_id": self.company_id.id})
        )
        duration = reservation._onchange_check_dates(
            checkin_date=checkin_dt, checkout_date=checkout_dt
        ).get("duration")
        return int(duration or 0)

    def _hotel_room_price(self, room, nights):
        """(untaxed, taxed) price of a room for the stay, as the folio prices
        it: the room's list price times the billable days."""
        self.ensure_one()
        currency = self.company_id.currency_id
        taxes = room.taxes_id.filtered(lambda tax: tax.company_id == self.company_id)
        if taxes:
            computed = taxes.compute_all(
                room.list_price,
                currency=currency,
                quantity=nights,
                product=room.product_id,
            )
            return computed["total_excluded"], computed["total_included"]
        amount = currency.round(room.list_price * nights)
        return amount, amount

    def _hotel_quote(self, entries, checkin_dt, checkout_dt):
        """Estimated price of a stay made of room types.

        :param entries: dicts with ``room_type``, ``qty`` and ``rooms`` (the
            rooms already assigned to that type, possibly none).

        Assigned rooms are priced as they are. Rooms still to be assigned
        are priced like the ones confirmation will pick - the cheapest free
        rooms of the type - so the estimate follows what the folio charges.
        Capacity counts the smallest room of the type, which is the most a
        request can promise before a room is assigned."""
        self.ensure_one()
        currency = self.company_id.currency_id
        room_obj = self.env["hotel.room"]
        nights = self._hotel_stay_nights(checkin_dt, checkout_dt)
        lines, untaxed, total, capacity = [], 0.0, 0.0, 0
        for entry in entries:
            room_type, qty = entry["room_type"], entry["qty"]
            assigned = (entry.get("rooms") or room_obj)[:qty]
            type_rooms = self._hotel_type_rooms(room_type)
            missing = qty - len(assigned)
            to_price = list(assigned)
            if missing > 0:
                candidates = (
                    self._hotel_free_rooms(room_type, checkin_dt, checkout_dt)
                    - assigned
                ) or type_rooms.sorted(lambda room: (room.list_price, room.name or ""))
                if candidates:
                    to_price += [
                        candidates[min(index, len(candidates) - 1)]
                        for index in range(missing)
                    ]
            line_untaxed = line_total = 0.0
            for room in to_price:
                room_untaxed, room_total = self._hotel_room_price(room, nights)
                line_untaxed += room_untaxed
                line_total += room_total
            capacity += sum(assigned.mapped("capacity")) + max(missing, 0) * min(
                type_rooms.mapped("capacity"), default=0
            )
            lines.append(
                {
                    "room_type": room_type,
                    "qty": qty,
                    "rooms": assigned,
                    "nights": nights,
                    "untaxed": currency.round(line_untaxed),
                    "total": currency.round(line_total),
                }
            )
            untaxed += line_untaxed
            total += line_total
        return {
            "lines": lines,
            "nights": nights,
            "untaxed": currency.round(untaxed),
            "tax": currency.round(total - untaxed),
            "total": currency.round(total),
            "currency": currency,
            "capacity": capacity,
            "room_count": sum(entry["qty"] for entry in entries),
        }

    def _hotel_reservation_summary(self, reservation):
        """Display values for a reservation, in the hotel's local time."""
        self.ensure_one()
        reservation = reservation.sudo()
        entries = {}
        for line in reservation.reservation_line:
            room_type = line.categ_id or line.reserve.room_categ_id[:1]
            if not room_type:
                continue
            entry = entries.setdefault(
                room_type.id,
                {
                    "room_type": room_type,
                    "qty": 0,
                    "rooms": self.env["hotel.room"].sudo(),
                },
            )
            entry["qty"] += max(len(line.reserve), 1)
            entry["rooms"] |= line.reserve
        checkin_local = self._hotel_local_datetime(reservation.checkin)
        checkout_local = self._hotel_local_datetime(reservation.checkout)
        return {
            "checkin_label": self._hotel_date_label(checkin_local.date()),
            "checkin_time": checkin_local.strftime("%H:%M"),
            "checkout_label": self._hotel_date_label(checkout_local.date()),
            "checkout_time": checkout_local.strftime("%H:%M"),
            "guests": [
                (
                    guest.name,
                    self.env._("Child")
                    if guest.guest_type == "child"
                    else self.env._("Adult"),
                )
                for guest in reservation.guest_ids
            ],
            "quote": self._hotel_quote(
                list(entries.values()), reservation.checkin, reservation.checkout
            ),
            "awaiting_confirmation": reservation.state == "draft",
        }
