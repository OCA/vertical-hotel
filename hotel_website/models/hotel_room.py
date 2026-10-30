# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HotelRoom(models.Model):
    _inherit = "hotel.room"

    # A dedicated flag rather than the product's own is_published: rooms are
    # sellable products, and publishing them would also list them in /shop.
    website_booking_published = fields.Boolean(
        "Bookable on Website",
        default=True,
        help="Count this room in the availability of its room type on the "
        "website, and allow it to be assigned to online requests.",
    )

    @api.model
    def _hotel_busy_room_ids(self, checkin_dt, checkout_dt, rooms):
        """Ids of ``rooms`` that already have a stay overlapping the period:
        the same rule the back office uses (hotel_reservation's
        ``hotel.room._get_booked_rooms``: confirmed reservations and folios,
        a stay ending when the next one starts does not block it)."""
        if not rooms:
            return set()
        booked = self.sudo()._get_booked_rooms(checkin_dt, checkout_dt)
        return set((booked & rooms.sudo()).ids)

    @api.model
    def _hotel_website_rooms(self, room_type, company):
        return self.sudo().search(
            [
                ("room_categ_id", "=", room_type.id),
                ("website_booking_published", "=", True),
                ("company_id", "in", [False, company.id]),
            ]
        )

    @api.model
    def _hotel_website_free_rooms(self, room_type, checkin_dt, checkout_dt, company):
        """Bookable rooms of a type free for the whole stay, cheapest first."""
        rooms = self._hotel_website_rooms(room_type, company)
        busy = self._hotel_busy_room_ids(checkin_dt, checkout_dt, rooms)
        return rooms.filtered(lambda room: room.id not in busy).sorted(
            lambda room: (room.list_price, -room.capacity, room.name or "")
        )
