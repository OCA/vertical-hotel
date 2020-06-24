# See LICENSE file for full copyright and licensing details.

import datetime
import time

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class HotelFolioLine(models.Model):
    @api.multi
    def copy(self, default=None):
        """
        @param self: object pointer
        @param default: dict of default values to be set
        """
        return super(HotelFolioLine, self).copy(default=default)

    @api.model
    def _get_checkin_date(self):
        if "checkin" in self._context:
            return self._context["checkin"]
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _get_checkout_date(self):
        if "checkout" in self._context:
            return self._context["checkout"]
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    _name = "hotel.folio.line"
    _description = "hotel folio1 room line"

    order_line_id = fields.Many2one(
        "sale.order.line",
        string="Order Line",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    folio_id = fields.Many2one(
        "hotel.folio", string="Folio", ondelete="cascade"
    )
    checkin_date = fields.Datetime(
        "Check In", required=True, default=_get_checkin_date
    )
    checkout_date = fields.Datetime(
        "Check Out", required=True, default=_get_checkout_date
    )
    is_reserved = fields.Boolean(
        "Is Reserved",
        help="True when folio line created from \
                                 Reservation",
    )

    @api.model
    def create(self, vals, check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio line.
        """
        if "folio_id" in vals:
            folio = self.env["hotel.folio"].browse(vals["folio_id"])
            vals.update({"order_id": folio.order_id.id})
        return super(HotelFolioLine, self).create(vals)

    @api.constrains("checkin_date", "checkout_date")
    def check_dates(self):
        """
        This method is used to validate the checkin_date and checkout_date.
        -------------------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        if self.checkin_date >= self.checkout_date:
            raise ValidationError(
                _(
                    "Room line Check In Date Should be \
                less than the Check Out Date!"
                )
            )
        if self.folio_id.date_order and self.checkin_date:
            if self.checkin_date <= self.folio_id.date_order:
                raise ValidationError(
                    _(
                        "Room line check in date should be \
                greater than the current date."
                    )
                )

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        sale_line_obj = self.env["sale.order.line"]
        fr_obj = self.env["folio.room.line"]
        for line in self:
            if line.order_line_id:
                sale_unlink_obj = sale_line_obj.browse([line.order_line_id.id])
                for rec in sale_unlink_obj:
                    room_obj = self.env["hotel.room"].search(
                        [("name", "=", rec.name)]
                    )
                    if room_obj.id:
                        folio_arg = [
                            ("folio_id", "=", line.folio_id.id),
                            ("room_id", "=", room_obj.id),
                        ]
                        folio_room_line_myobj = fr_obj.search(folio_arg)
                        if folio_room_line_myobj.id:
                            folio_room_line_myobj.unlink()
                            room_obj.write(
                                {"isroom": True, "status": "available"}
                            )
                sale_unlink_obj.unlink()
        return super(HotelFolioLine, self).unlink()

    @api.onchange("product_id")
    def product_id_change(self):
        """
 -        @param self: object pointer
 -        """
        context = dict(self._context)
        if not context:
            context = {}
        if context.get("folio", False):
            if self.product_id and self.folio_id.partner_id:
                self.name = self.product_id.name
                self.price_unit = self.product_id.list_price
                self.product_uom = self.product_id.uom_id
                tax_obj = self.env["account.tax"]
                pr = self.product_id
                self.price_unit = tax_obj._fix_tax_included_price(
                    pr.price, pr.taxes_id, self.tax_id
                )
        else:
            if not self.product_id:
                return {"domain": {"product_uom": []}}
            val = {}
            pr = self.product_id.with_context(
                lang=self.folio_id.partner_id.lang,
                partner=self.folio_id.partner_id.id,
                quantity=val.get("product_uom_qty") or self.product_uom_qty,
                date=self.folio_id.date_order,
                pricelist=self.folio_id.pricelist_id.id,
                uom=self.product_uom.id,
            )
            p = pr.with_context(pricelist=self.order_id.pricelist_id.id).price
            if self.folio_id.pricelist_id and self.folio_id.partner_id:
                obj = self.env["account.tax"]
                val["price_unit"] = obj._fix_tax_included_price(
                    p, pr.taxes_id, self.tax_id
                )

    @api.onchange("checkin_date", "checkout_date")
    def on_change_checkout(self):
        """
        When you change checkin_date or checkout_date it will checked it
        and update the qty of hotel folio line
        -----------------------------------------------------------------
        @param self: object pointer
        """
        configured_addition_hours = 0
        fwhouse_id = self.folio_id.warehouse_id
        fwc_id = fwhouse_id or fwhouse_id.company_id
        if fwc_id:
            configured_addition_hours = fwhouse_id.company_id.additional_hours
        myduration = 0
        if not self.checkin_date:
            self.checkin_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout_date:
            self.checkout_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        chckin = self.checkin_date
        chckout = self.checkout_date
        if chckin and chckout:
            server_dt = DEFAULT_SERVER_DATETIME_FORMAT
            chkin_dt = datetime.datetime.strptime(chckin, server_dt)
            chkout_dt = datetime.datetime.strptime(chckout, server_dt)
            dur = chkout_dt - chkin_dt
            sec_dur = dur.seconds
            if (not dur.days and not sec_dur) or (dur.days and not sec_dur):
                myduration = dur.days
            else:
                myduration = dur.days + 1
            #            To calculate additional hours in hotel room as per minutes
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    myduration += 1
        self.product_uom_qty = myduration
        hotel_room_obj = self.env["hotel.room"]
        hotel_room_ids = hotel_room_obj.search([])
        avail_prod_ids = []
        for room in hotel_room_ids:
            assigned = False
            for rm_line in room.room_line_ids:
                if rm_line.status != "cancel":
                    if (
                        self.checkin_date
                        <= rm_line.check_in
                        <= self.checkout_date
                    ) or (
                        self.checkin_date
                        <= rm_line.check_out
                        <= self.checkout_date
                    ):
                        assigned = True
                    elif (
                        rm_line.check_in
                        <= self.checkin_date
                        <= rm_line.check_out
                    ) or (
                        rm_line.check_in
                        <= self.checkout_date
                        <= rm_line.check_out
                    ):
                        assigned = True
            if not assigned:
                avail_prod_ids.append(room.product_id.id)
        domain = {"product_id": [("id", "in", avail_prod_ids)]}
        return {"domain": domain}

    @api.multi
    def button_confirm(self):
        """
        @param self: object pointer
        """
        for folio in self:
            line = folio.order_line_id
            line.button_confirm()
        return True

    @api.multi
    def button_done(self):
        """
        @param self: object pointer
        """
        lines = [folio_line.order_line_id for folio_line in self]
        lines.button_done()
        self.state = "done"
        return True

    @api.multi
    def copy_data(self, default=None):
        """
        @param self: object pointer
        @param default: dict of default values to be set
        """
        line_id = self.order_line_id.id
        sale_line_obj = self.env["sale.order.line"].browse(line_id)
        return sale_line_obj.copy_data(default=default)
