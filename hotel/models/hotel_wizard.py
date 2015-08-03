from openerp import fields
from openerp import models


class sale_advance_payment_inv(models.Model):
    _inherit = "sale.advance.payment.inv"
    _name = "hotel.wizard"

    @api.model
    def create_invoices(self, cr, uid, ids, context=None):
        ctx = dict(
            active_ids=self.env['hotel.folio'].browse(active_ids).sale_id
        )
        return super(
            sale_advance_payment_inv, self
        ).create_invoices(context=ctx)
