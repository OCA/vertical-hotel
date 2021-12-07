from odoo import api, models, fields


class AccountMove(models.Model):

    _inherit = "account.move"

    is_folio = fields.Boolean(string="Is folio", default=False)
    folio_id = fields.Many2one(comodel_name="hotel.folio", string="Corresponding folio")

    @api.model
    def create(self, vals):
        if self._context.get("folio_id"):
            folio = self.env["hotel.folio"].browse(self._context["folio_id"])
            vals.update({"is_folio": True, "folio_id": folio.id})
            res = super(AccountMove, self).create(vals)
            folio.write(
                {"hotel_invoice_id": res.id, "invoice_status": "invoiced"}
            )
            return res
        else:
            return super(AccountMove, self).create(vals)

    def open_folio_from_invoice(self):
        rec = self.ensure_one()
        if not rec.is_folio:
            return
        action = self.env.ref("hotel.open_hotel_folio1_form_tree_all").read()[0]
        action['views'] = [(self.env.ref('hotel.view_hotel_folio_form').id, 'form')]
        action["res_id"] = rec.folio_id.id
        return action
