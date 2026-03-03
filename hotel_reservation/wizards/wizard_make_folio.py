# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MakeFolioWizard(models.TransientModel):
    _name = "wizard.make.folio"
    _description = "Allow to generate the folio"

    grouped = fields.Boolean(
        string="Group the Folios",
    )

    def make_folios(self):
        Reservation = self.env["hotel.reservation"]
        newinv = [
            order.id
            for order in Reservation.browse(
                self.env.context.get("active_ids", [])
            ).mapped("folio_id")
        ]
        return {
            "domain": "[('id','in', [" + ",".join(map(str, newinv)) + "])]",
            "name": "Folios",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "hotel.folio",
            "view_id": False,
            "type": "ir.actions.act_window",
        }
