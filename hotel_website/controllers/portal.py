# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class HotelReservationPortal(CustomerPortal):
    def _hotel_reservation_domain(self):
        partner = request.env.user.partner_id
        # A desk draft is the front desk's work in progress, not something
        # the guest asked for; a website request is, even before it is
        # confirmed.
        return [
            ("partner_id", "child_of", partner.commercial_partner_id.id),
            "|",
            ("state", "!=", "draft"),
            ("is_website_booking", "=", True),
        ]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "hotel_reservation_count" in counters:
            # Portal users have no access right on hotel.reservation; the
            # domain above is what restricts them to their own stays.
            values["hotel_reservation_count"] = (
                request.env["hotel.reservation"]
                .sudo()
                .search_count(self._hotel_reservation_domain())
            )
        return values

    @http.route(
        ["/my/reservations", "/my/reservations/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_hotel_reservations(self, page=1, sortby=None, **kwargs):
        reservations_sudo = request.env["hotel.reservation"].sudo()
        domain = self._hotel_reservation_domain()
        searchbar_sortings = {
            "checkin": {"label": request.env._("Arrival"), "order": "checkin desc"},
            "number": {
                "label": request.env._("Reservation Number"),
                "order": "reservation_no desc",
            },
        }
        if sortby not in searchbar_sortings:
            sortby = "checkin"
        pager = portal_pager(
            url="/my/reservations",
            url_args={"sortby": sortby},
            total=reservations_sudo.search_count(domain),
            page=page,
            step=self._items_per_page,
        )
        reservations = reservations_sudo.search(
            domain,
            order=searchbar_sortings[sortby]["order"],
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        website = request.env.website
        values = self._prepare_portal_layout_values()
        values.update(
            {
                "reservations": reservations,
                "summaries": {
                    reservation.id: website._hotel_reservation_summary(reservation)
                    for reservation in reservations
                },
                "page_name": "hotel_reservation",
                "pager": pager,
                "default_url": "/my/reservations",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("hotel_website.portal_my_reservations", values)

    @http.route(
        ["/my/reservations/<int:reservation_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_hotel_reservation(self, reservation_id, **kwargs):
        reservation = (
            request.env["hotel.reservation"]
            .sudo()
            .search(self._hotel_reservation_domain() + [("id", "=", reservation_id)])
        )
        if not reservation:
            return request.redirect("/my")
        values = self._prepare_portal_layout_values()
        values.update(
            {
                "reservation": reservation,
                "summary": request.env.website._hotel_reservation_summary(reservation),
                "page_name": "hotel_reservation",
            }
        )
        return request.render("hotel_website.portal_hotel_reservation_page", values)
