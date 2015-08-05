from openerp import models
from openerp import api


class sale_advance_payment_inv(models.Model):
    _inherit = ['sale.advance.payment.inv']

    @api.multi
    def create_invoices(self, context=None):
        active_order_id = self.env['hotel.folio'].browse(
            context.get('active_ids', [])).order_id.id
        context["active_ids"] = [active_order_id]
        context["active_id"] = active_order_id
        super(
            sale_advance_payment_inv, self.with_context(context)
        ).create_invoices()
