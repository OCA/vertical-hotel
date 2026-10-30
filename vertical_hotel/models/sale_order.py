# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    folio_ids = fields.One2many(
        "hotel.folio",
        "order_id",
        string="Folios",
        help="Hotel folio(s) this order was generated for.",
    )
    is_folio_order = fields.Boolean(
        "Created from Folio",
        compute="_compute_is_folio_order",
        store=True,
        readonly=True,
        help="Set automatically when the order belongs to a hotel folio. "
        "Such an order must be confirmed from the folio, so the room "
        "and guest capacity checks are not skipped.",
    )

    @api.depends("folio_ids")
    def _compute_is_folio_order(self):
        for order in self:
            order.is_folio_order = bool(order.folio_ids)

    def action_confirm(self):
        """Refuse to confirm a folio's order from the Sales side.

        hotel.folio.action_confirm() checks the guests against the room
        capacity first and then confirms the order with the
        ``hotel_folio_confirm`` context key, so this only catches someone
        confirming the order directly - which would skip that check."""
        if self.env.context.get("hotel_folio_confirm"):
            return super().action_confirm()
        for order in self:
            if order.is_folio_order:
                raise ValidationError(
                    order.env._(
                        "This is a hotel folio's sales order (%(folio)s).\n"
                        "Confirm it from the folio instead - confirming it "
                        "here would skip the room capacity and guest checks.",
                        folio=", ".join(order.folio_ids.mapped("name")),
                    )
                )
        return super().action_confirm()
