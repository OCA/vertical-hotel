# -*- coding: utf-8 -*-
from openerp import api
from openerp import models


class SaleAdvancePaymentInv(models.Model):
    _inherit = ['sale.advance.payment.inv']

    @api.multi
    def create_invoices(self, context=None):
        active_order_id = self.env['hotel.folio'].browse(
            context.get('active_ids', [])).order_id.id
        context["active_ids"] = [active_order_id]
        context["active_id"] = active_order_id
        super(
            SaleAdvancePaymentInv, self.with_context(context)
        ).create_invoices()
