# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.fields import Domain


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _get_available_room_domain(self, checkin_date, checkout_date):
        """Rooms offered on a folio line: also leave out the rooms of
        confirmed reservations that have no folio yet (the others are
        already on their folio's room lines)."""
        domain = super()._get_available_room_domain(checkin_date, checkout_date)
        reserved = self.env["hotel.room"]._get_booked_rooms(
            checkin_date,
            checkout_date,
            include_folios=False,
            reservation_states=("confirm",),
        )
        return Domain.AND([domain, [("id", "not in", reserved.product_id.ids)]])
