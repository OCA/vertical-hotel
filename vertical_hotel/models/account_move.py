# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        """Link the invoice created from a folio's "Create Invoice" wizard
        (context key ``folio_id``) to that folio."""
        moves = super().create(vals_list)
        folio_id = self.env.context.get("folio_id")
        if folio_id and moves:
            self.env["hotel.folio"].browse(folio_id).hotel_invoice_id = moves[-1]
        return moves
