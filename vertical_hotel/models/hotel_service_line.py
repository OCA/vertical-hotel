# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import ClassVar

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HotelServiceLine(models.Model):
    _name = "hotel.service.line"
    _description = "Hotel service line"
    _inherits: ClassVar[dict] = {"sale.order.line": "service_line_id"}

    service_line_id = fields.Many2one(
        "sale.order.line",
        required=True,
        ondelete="cascade",
    )
    folio_id = fields.Many2one("hotel.folio", ondelete="cascade")
    ser_checkin_date = fields.Datetime("From Date")
    ser_checkout_date = fields.Datetime("To Date")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel service line.
        """
        folio_obj = self.env["hotel.folio"]
        for vals in vals_list:
            if "folio_id" in vals:
                folio = folio_obj.browse(vals.get("folio_id"))
                vals.update({"order_id": folio.order_id.id})
        return super().create(vals_list)

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        service_line_ids = self.mapped("service_line_id")

        res = super().unlink()

        if service_line_ids:
            service_line_ids.unlink()

        return res

    # Migrated _onchange_product_id method v15 to v18.
    @api.onchange("product_id")
    def _onchange_product_id_warning(self):
        self.ensure_one()
        if not self.product_id or not self.service_line_id:
            return
        product = self.product_id
        company = self.company_id or self.order_id.company_id or self.env.company
        taxes = product.taxes_id._filter_taxes_by_company(company)
        self.update(
            {
                "name": product.name,
                "product_uom_id": product.uom_id,
                "product_uom_qty": self.product_uom_qty,
                "price_unit": product.list_price,
                "tax_ids": self.order_id.fiscal_position_id.map_tax(taxes),
            }
        )
        if product.sale_line_warn_msg:
            return {
                "warning": {
                    "title": self.env._("Warning for %s", product.name),
                    "message": product.sale_line_warn_msg,
                }
            }

    @api.onchange("ser_checkin_date", "ser_checkout_date")
    def _on_change_checkin_checkout_dates(self):
        """
        When you change checkin_date or checkout_date it will checked it
        and update the qty of hotel service line
        -----------------------------------------------------------------
        @param self: object pointer
        """
        now = fields.Datetime.now()
        if not self.ser_checkin_date:
            self.ser_checkin_date = now
        if not self.ser_checkout_date:
            self.ser_checkout_date = self.ser_checkin_date
        if self.ser_checkout_date < self.ser_checkin_date:
            raise ValidationError(
                self.env._("Checkout must be greater or equal checkin date")
            )
        if self.ser_checkin_date and self.ser_checkout_date:
            diffDate = self.ser_checkout_date - self.ser_checkin_date
            qty = diffDate.days + 1
            self.product_uom_qty = qty

    def copy_data(self, default=None):
        """
        @param self: object pointer
        @param default: dict of default values to be set
        """
        return self.service_line_id.copy_data(default=default)
