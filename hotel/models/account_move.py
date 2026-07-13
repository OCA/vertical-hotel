# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides orm create method
        to link the account move with a hotel folio.
        """
        rec = super().create(vals_list)
        active_id = self.env.context.get("folio_id")
        if active_id:
            folio = self.env["hotel.folio"].browse(active_id)
            for res in rec:
                folio.write({"hotel_invoice_id": res.id, "invoice_status": "invoiced"})
        return rec
