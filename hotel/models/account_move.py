# Copyright (C) 2023-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):

    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        folio_id = self._context.get("folio_id")
        if folio_id:
            folio = self.env["hotel.folio"].browse(folio_id)
            folio.write(
                {"hotel_invoice_id": [(6, 0, res.ids)], "invoice_status": "invoiced"}
            )

        return res
