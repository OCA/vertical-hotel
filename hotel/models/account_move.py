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
        folio_obj = self.env["hotel.folio"]
        active_id = self._context.get("folio_id")
        for res in rec:
            if active_id:
                folio = folio_obj.browse(active_id)
                folio.write({"hotel_invoice_id": res.id, "invoice_status": "invoiced"})
        return rec
