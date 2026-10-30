# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HotelGuest(models.Model):
    _inherit = "hotel.guest"

    reservation_id = fields.Many2one(
        "hotel.reservation",
        ondelete="cascade",
        index=True,
    )

    @api.model
    def _resolve_host_partner(self, vals):
        """A guest added on a reservation is filed under the person who
        made the reservation."""
        if vals.get("reservation_id"):
            return (
                self.env["hotel.reservation"].browse(vals["reservation_id"]).partner_id
            )
        return super()._resolve_host_partner(vals)
