# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Domain


class ProductProduct(models.Model):
    _inherit = "product.product"

    isroom = fields.Boolean("Is Room")
    iscategid = fields.Boolean("Is Categ")
    isservice = fields.Boolean("Is Service")

    @api.model
    def _get_available_room_domain(self, checkin_date, checkout_date):
        """Domain on product.product matching the rooms that have no
        booking overlapping [checkin_date, checkout_date).

        Two stays overlap when one starts before the other ends; a stay
        ending exactly when the next one starts does not block it (same
        rule as hotel.folio's double-booking constraint)."""
        busy_rooms = (
            self.env["folio.room.line"]
            .sudo()
            .search(
                [
                    ("check_in", "<", checkout_date),
                    ("check_out", ">", checkin_date),
                    ("folio_id.state", "!=", "cancel"),
                ]
            )
            .room_id
        )
        free_rooms = (
            self.env["hotel.room"]
            .sudo()
            .with_context(active_test=False)
            .search([("id", "not in", busy_rooms.ids)])
        )
        return [("id", "in", free_rooms.product_id.ids)]

    @api.model
    def search_fetch(self, domain, field_names=None, offset=0, limit=None, order=None):
        """With context["from_room"] and check-in/out dates, only return the
        rooms that are free on those dates."""
        context = self.env.context
        if context.get("from_room"):
            checkin_date = context.get("checkin_date")
            checkout_date = context.get("checkout_date")
            if isinstance(checkin_date, str):
                checkin_date = fields.Datetime.from_string(checkin_date)
            if isinstance(checkout_date, str):
                checkout_date = fields.Datetime.from_string(checkout_date)
            if checkin_date and checkout_date:
                domain = Domain.AND(
                    [
                        domain,
                        self._get_available_room_domain(checkin_date, checkout_date),
                    ]
                )
        return super().search_fetch(
            domain, field_names, offset=offset, limit=limit, order=order
        )
