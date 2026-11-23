# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    folio_ids = fields.One2many(
        "hotel.folio",
        "order_id",
        string="Folios",
        help="Hotel folio(s) this order was generated for.",
    )

    def action_confirm(self):
        """Check the guests against the room capacity of the folios first.

        Done here rather than on the folio so that every way an order gets
        confirmed - the folio button, the Sales order, an online payment
        (sale's payment flow calls action_confirm() directly) - runs the
        same check instead of being refused or skipping it."""
        self.folio_ids._check_guest_capacity()
        return super().action_confirm()
