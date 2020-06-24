# See LICENSE file for full copyright and licensing details.

import datetime
import time

from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class HotelServiceLine(models.Model):
    @api.multi
    def copy(self, default=None):
        """
        @param self: object pointer
        @param default: dict of default values to be set
        """
        return super(HotelServiceLine, self).copy(default=default)

    @api.model
    def _service_checkin_date(self):
        if "checkin" in self._context:
            return self._context["checkin"]
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _service_checkout_date(self):
        if "checkout" in self._context:
            return self._context["checkout"]
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    _name = "hotel.service.line"
    _description = "hotel Service line"

    service_line_id = fields.Many2one(
        "sale.order.line",
        "Service Line",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    folio_id = fields.Many2one("hotel.folio", "Folio", ondelete="cascade")
    ser_checkin_date = fields.Datetime(
        "From Date", required=True, default=_service_checkin_date
    )
    ser_checkout_date = fields.Datetime(
        "To Date", required=True, default=_service_checkout_date
    )

    @api.model
    def create(self, vals, check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel service line.
        """
        if "folio_id" in vals:
            folio = self.env["hotel.folio"].browse(vals["folio_id"])
            vals.update({"order_id": folio.order_id.id})
        return super(HotelServiceLine, self).create(vals)

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        s_line_obj = self.env["sale.order.line"]
        for line in self:
            if line.service_line_id:
                sale_unlink_obj = s_line_obj.browse([line.service_line_id.id])
                sale_unlink_obj.unlink()
        return super(HotelServiceLine, self).unlink()

    @api.onchange("product_id")
    def product_id_change(self):
        """
        @param self: object pointer
        """
        if self.product_id and self.folio_id.partner_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.list_price
            self.product_uom = self.product_id.uom_id
            tax_obj = self.env["account.tax"]
            prod = self.product_id
            self.price_unit = tax_obj._fix_tax_included_price(
                prod.price, prod.taxes_id, self.tax_id
            )

    @api.onchange("ser_checkin_date", "ser_checkout_date")
    def on_change_checkout(self):
        """
        When you change checkin_date or checkout_date it will checked it
        and update the qty of hotel service line
        -----------------------------------------------------------------
        @param self: object pointer
        """
        if not self.ser_checkin_date:
            time_a = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            self.ser_checkin_date = time_a
        if not self.ser_checkout_date:
            self.ser_checkout_date = time_a
        if self.ser_checkout_date < self.ser_checkin_date:
            raise _("Checkout must be greater or equal checkin date")
        if self.ser_checkin_date and self.ser_checkout_date:
            date_a = time.strptime(
                self.ser_checkout_date, DEFAULT_SERVER_DATETIME_FORMAT
            )[:5]
            date_b = time.strptime(
                self.ser_checkin_date, DEFAULT_SERVER_DATETIME_FORMAT
            )[:5]
            diffDate = datetime.datetime(*date_a) - datetime.datetime(*date_b)
            qty = diffDate.days + 1
            self.product_uom_qty = qty

    @api.multi
    def button_confirm(self):
        """
        @param self: object pointer
        """
        for folio in self:
            line = folio.service_line_id
            x = line.button_confirm()
        return x

    @api.multi
    def button_done(self):
        """
        @param self: object pointer
        """
        for folio in self:
            line = folio.service_line_id
            x = line.button_done()
        return x

    @api.multi
    def copy_data(self, default=None):
        """
        @param self: object pointer
        @param default: dict of default values to be set
        """
        sale_line_obj = self.env["sale.order.line"].browse(
            self.service_line_id.id
        )
        return sale_line_obj.copy_data(default=default)
