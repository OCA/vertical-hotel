# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(
        [
            ("delivered", "Regular invoice"),
            ("percentage", "Down payment (percentage)"),
            ("fixed", "Down payment (fixed amount)"),
        ],
        string="Create Invoice",
        default="delivered",
        required=True,
        help="""A standard invoice is issued with all the order lines ready for
        invoicing, according to their invoicing policy
        (based on ordered or delivered quantity).""",
    )

    def create_invoices(self):
        ctx = self.env.context.copy()
        if self._context.get("active_model") == "hotel.folio":

            HotelFolio = self.env["hotel.folio"]
            folio = HotelFolio.browse(self._context.get("active_ids", []))
            folio.room_line_ids.mapped("product_id").write({"isroom": True})
            ctx.update(
                {
                    "active_ids": folio.order_id.ids,
                    "active_id": folio.order_id.id,
                    "folio_id": folio.id,
                }
            )
        res = super(SaleAdvancePaymentInv, self.with_context(**ctx)).create_invoices()

        return res
