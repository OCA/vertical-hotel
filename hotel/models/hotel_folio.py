# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


def _offset_format_timestamp1(
    src_tstamp_str,
    src_format,
    dst_format,
    ignore_unparsable_time=True,
    context=None,
):
    """
    Convert a source timeStamp string into a destination timeStamp string,
    attempting to apply the correct offset if both the server and local
    timeZone are recognized,or no offset at all if they aren't or if
    tz_offset is false (i.e. assuming they are both in the same TZ).
    @param src_tstamp_str: the STR value containing the timeStamp.
    @param src_format: the format to use when parsing the local timeStamp.
    @param dst_format: the format to use when formatting the resulting
     timeStamp.
    @param server_to_client: specify timeZone offset direction (server=src
                             and client=dest if True, or client=src and
                             server=dest if False)
    @param ignore_unparsable_time: if True, return False if src_tstamp_str
                                   cannot be parsed using src_format or
                                   formatted using dst_format.
    @return: destination formatted timestamp, expressed in the destination
             timezone if possible and if tz_offset is true, or src_tstamp_str
             if timezone offset could not be determined.
    """
    if not src_tstamp_str:
        return False
    res = src_tstamp_str
    if src_format and dst_format:
        try:
            # dt_value needs to be a datetime object\
            # (so notime.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.strptime(src_tstamp_str, src_format)
            if context.get("tz", False):
                try:
                    import pytz

                    src_tz = pytz.timezone(context["tz"])
                    dst_tz = pytz.timezone("UTC")
                    src_dt = src_tz.localize(dt_value, is_dst=True)
                    dt_value = src_dt.astimezone(dst_tz)
                except Exception:
                    pass
            res = dt_value.strftime(dst_format)
        except Exception:
            # Normal ways to end up here are if strptime or strftime failed
            if not ignore_unparsable_time:
                return False
            pass
    return res


class FolioRoomLine(models.Model):

    _name = "folio.room.line"
    _description = "Hotel Room Reservation"
    _rec_name = "room_id"

    room_id = fields.Many2one("hotel.room", "Room id")
    check_in = fields.Datetime("Check In Date", required=True)
    check_out = fields.Datetime("Check Out Date", required=True)
    folio_id = fields.Many2one("hotel.folio", "Folio Number")
    status = fields.Selection(string="state", related="folio_id.state")


class HotelFolio(models.Model):

    _name = "hotel.folio"
    _description = "hotel folio new"
    _rec_name = "order_id"

    def name_get(self):
        res = []
        fname = ""
        for rec in self:
            if rec.order_id:
                fname = str(rec.name)
                res.append((rec.id, fname))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        args += [("name", operator, name)]
        folio = self.search(args, limit=100)
        return folio.name_get()

    @api.model
    def _get_checkin_date(self):
        if self._context.get("tz"):
            to_zone = self._context.get("tz")
        else:
            to_zone = "UTC"
        return _offset_format_timestamp1(
            time.strftime("%Y-%m-%d 12:00:00"),
            DEFAULT_SERVER_DATETIME_FORMAT,
            DEFAULT_SERVER_DATETIME_FORMAT,
            ignore_unparsable_time=True,
            context={"tz": to_zone},
        )

    @api.model
    def _get_checkout_date(self):
        if self._context.get("tz"):
            to_zone = self._context.get("tz")
        else:
            to_zone = "UTC"
        tm_delta = timedelta(days=1)
        return (
            datetime.strptime(
                _offset_format_timestamp1(
                    time.strftime("%Y-%m-%d 12:00:00"),
                    DEFAULT_SERVER_DATETIME_FORMAT,
                    DEFAULT_SERVER_DATETIME_FORMAT,
                    ignore_unparsable_time=True,
                    context={"tz": to_zone},
                ),
                "%Y-%m-%d %H:%M:%S",
            )
            + tm_delta
        )

    name = fields.Char(
        "Folio Number", readonly=True, index=True, default="New"
    )
    order_id = fields.Many2one(
        "sale.order", "Order", delegate=True, required=True, ondelete="cascade"
    )
    checkin_date = fields.Datetime(
        "Check In",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=_get_checkin_date,
    )
    checkout_date = fields.Datetime(
        "Check Out",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=_get_checkout_date,
    )
    room_line_ids = fields.One2many(
        "hotel.folio.line",
        "folio_id",
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        help="Hotel room reservation detail.",
    )
    service_line_ids = fields.One2many(
        "hotel.service.line",
        "folio_id",
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        help="Hotel services details provided to"
        "Customer and it will included in "
        "the main Invoice.",
    )
    hotel_policy = fields.Selection(
        [
            ("prepaid", "On Booking"),
            ("manual", "On Check In"),
            ("picking", "On Checkout"),
        ],
        "Hotel Policy",
        default="manual",
        help="Hotel policy for payment that "
        "either the guest has to payment at "
        "booking time or check-in "
        "check-out time.",
    )
    duration = fields.Float(
        "Duration in Days",
        help="Number of days which will automatically "
        "count from the check-in and check-out date. ",
    )
    hotel_invoice_id = fields.Many2one("account.move", "Invoice", copy=False)
    duration_dummy = fields.Float("Duration Dummy")

    @api.constrains("room_line_ids")
    def folio_room_lines(self):
        """
        This method is used to validate the room_lines.
        ------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        for rec in self:
            for room_no in rec.room_line_ids.mapped("product_id"):
                for line in rec.room_line_ids:
                    record = line.search(
                        [
                            ("product_id", "=", room_no.id),
                            ("folio_id", "=", rec.id),
                            ("id", "!=", line.id),
                            ("checkin_date", ">=", line.checkin_date),
                            ("checkout_date", "<=", line.checkout_date),
                            ("product_id", "=", room_no.id),
                        ]
                    )

                if record:
                    raise ValidationError(
                        _(
                            """Room Duplicate Exceeded!, """
                            """You Cannot Take Same %s Room Twice!"""
                        )
                        % (room_no.name)
                    )

    @api.onchange("checkout_date", "checkin_date")
    def onchange_dates(self):
        """
        This method gives the duration between check in and checkout
        if customer will leave only for some hour it would be considers
        as a whole day.If customer will check in checkout for more or equal
        hours, which configured in company as additional hours than it would
        be consider as full days
        --------------------------------------------------------------------
        @param self: object pointer
        @return: Duration and checkout_date
        """
        configured_addition_hours = (
            self.warehouse_id.company_id.additional_hours
        )
        myduration = 0
        if self.checkout_date and self.checkin_date:
            dur = self.checkin_date - self.checkin_date
            sec_dur = dur.seconds
            if (not dur.days and not sec_dur) or (dur.days and not sec_dur):
                myduration = dur.days
            else:
                myduration = dur.days + 1
            # To calculate additional hours in hotel room as per minutes
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    myduration += 1
        self.duration = myduration
        self.duration_dummy = self.duration

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio.
        """
        if not "service_line_ids" and "folio_id" in vals:
            tmp_room_lines = vals.get("room_line_ids", [])
            vals["order_policy"] = vals.get("hotel_policy", "manual")
            vals.update({"room_line_ids": []})
            folio_id = super(HotelFolio, self).create(vals)
            for line in tmp_room_lines:
                line[2].update({"folio_id": folio_id.id})
            vals.update({"room_line_ids": tmp_room_lines})
            folio_id.write(vals)
        else:
            if not vals:
                vals = {}
            vals["name"] = self.env["ir.sequence"].next_by_code("hotel.folio")
            vals["duration"] = vals.get("duration", 0.0) or vals.get(
                "duration_dummy", 0.0
            )
            folio_id = super(HotelFolio, self).create(vals)
            folio_room_line_obj = self.env["folio.room.line"]
            h_room_obj = self.env["hotel.room"]
            try:
                for rec in folio_id:
                    if not rec.reservation_id:
                        for room_rec in rec.room_line_ids:
                            room = h_room_obj.search(
                                [("product_id", "=", room_rec.product_id.id)]
                            )
                            room.write({"isroom": False})
                            vals = {
                                "room_id": room.id,
                                "check_in": rec.checkin_date,
                                "check_out": rec.checkout_date,
                                "folio_id": rec.id,
                            }
                            folio_room_line_obj.create(vals)
            except Exception:
                for rec in folio_id:
                    for room_rec in rec.room_line_ids:
                        room = h_room_obj.search(
                            [("product_id", "=", room_rec.product_id.id)]
                        )
                        room.write({"isroom": False})
                        vals = {
                            "room_id": room.id,
                            "check_in": rec.checkin_date,
                            "check_out": rec.checkout_date,
                            "folio_id": rec.id,
                        }
                        folio_room_line_obj.create(vals)
        return folio_id

    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        product_obj = self.env["product.product"]
        h_room_obj = self.env["hotel.room"]
        folio_room_line_obj = self.env["folio.room.line"]
        for rec in self:
            rooms_list = [res.product_id.id for res in rec.room_line_ids]
            if vals and vals.get("duration_dummy", False):
                vals["duration"] = vals.get("duration_dummy", 0.0)
            else:
                vals["duration"] = rec.duration
            room_lst = [
                folio_rec.product_id.id for folio_rec in rec.room_line_ids
            ]
            new_rooms = set(room_lst).difference(set(rooms_list))
            if len(list(new_rooms)) != 0:
                room_list = product_obj.browse(list(new_rooms))
                for rm in room_list:
                    room_obj = h_room_obj.search([("name", "=", rm.name)])
                    room_obj.write({"isroom": False})
                    vals = {
                        "room_id": room_obj.id,
                        "check_in": rec.checkin_date,
                        "check_out": rec.checkout_date,
                        "folio_id": rec.id,
                    }
                    folio_room_line_obj.create(vals)
            if not len(list(new_rooms)):
                room_list_obj = product_obj.browse(rooms_list)
                for room in room_list_obj:
                    room_obj = h_room_obj.search(
                        [("product_id", "=", room.id)]
                    )
                    room_obj.write({"isroom": False})
                    room_vals = {
                        "room_id": room_obj.id,
                        "check_in": rec.checkin_date,
                        "check_out": rec.checkout_date,
                        "folio_id": rec.id,
                    }
                    folio_romline_rec = folio_room_line_obj.search(
                        [("folio_id", "=", rec.id)]
                    )
                    folio_romline_rec.write(room_vals)
        return super(HotelFolio, self).write(vals)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel folio as well
        ---------------------------------------------------------------
        @param self: object pointer
        """
        if self.partner_id:
            order_ids = [folio.order_id.id for folio in self]
            self.update(
                {
                    "partner_invoice_id": self.partner_id.id,
                    "partner_shipping_id": self.partner_id.id,
                    "pricelist_id": self.partner_id.property_product_pricelist.id,
                }
            )
            if not order_ids:
                raise ValidationError(
                    _("No Order found for  %s !") % (self.partner_id.name)
                )

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        """
        @param self: object pointer
        """
        if not self.order_id:
            raise UserError(_("Order id is not available"))
        self.invoice_ids.write({"state": "cancel"})
        return self.order_id.action_cancel()

    def action_confirm(self):
        for order in self.order_id:
            order.state = "sale"
            if not order.analytic_account_id:
                for line in order.order_line:
                    if line.product_id.invoice_policy == "cost":
                        order._create_analytic_account()
                        break
        config_parameter_obj = self.env["ir.config_parameter"]
        if config_parameter_obj.sudo().get_param("sale.auto_done_setting"):
            self.order_id.action_done()

    def action_cancel_draft(self):
        """
        @param self: object pointer
        """
        if not len(self._ids):
            return False
        query = "select id from sale_order_line \
        where order_id IN %s and state=%s"
        self._cr.execute(query, (tuple(self._ids), "cancel"))
        cr1 = self._cr
        line_ids = map(lambda x: x[0], cr1.fetchall())
        self.write({"state": "draft", "invoice_ids": []})
        sale_line_obj = self.env["sale.order.line"].browse(line_ids)
        sale_line_obj.write(
            {
                "invoiced": False,
                "state": "draft",
                "invoice_lines": [(6, 0, [])],
            }
        )
        return True


class HotelFolioLine(models.Model):

    _name = "hotel.folio.line"
    _description = "Hotel Folio Room Line"

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

    order_line_id = fields.Many2one(
        "sale.order.line",
        "Order Line",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    folio_id = fields.Many2one("hotel.folio", "Folio", ondelete="cascade")
    checkin_date = fields.Datetime(
        "Check In", required=True, default=_get_checkin_date
    )
    checkout_date = fields.Datetime(
        "Check Out", required=True, default=_get_checkout_date
    )
    is_reserved = fields.Boolean(
        "Is Reserved", help="True when folio line created from Reservation"
    )

    @api.model
    def create(self, vals):
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
                    """Room line Check In Date Should be """
                    """less than the Check Out Date!"""
                )
            )
        if self.folio_id.date_order and self.checkin_date:
            if self.checkin_date.date() < self.folio_id.date_order.date():
                raise ValidationError(
                    _(
                        """Room line check in date should be """
                        """greater than the current date."""
                    )
                )

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        for line in self:
            if line.order_line_id:
                rooms = self.env["hotel.room"].search(
                    [("product_id", "=", line.order_line_id.product_id.id)]
                )
                folio_room_lines = self.env["folio.room.line"].search(
                    [
                        ("folio_id", "=", line.folio_id.id),
                        ("room_id", "in", rooms.ids),
                    ]
                )
                folio_room_lines.unlink()
                rooms.write({"isroom": True, "status": "available"})
                line.order_line_id.unlink()
        return super(HotelFolioLine, self).unlink()

    def _get_real_price_currency(
        self, product, rule_id, qty, uom, pricelist_id
    ):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming
            from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sale order"""
        PricelistItem = self.env["product.pricelist.item"]
        field_name = "lst_price"
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if (
                pricelist_item.pricelist_id.discount_policy
                == "without_discount"
            ):
                while (
                    pricelist_item.base == "pricelist"
                    and pricelist_item.base_pricelist_id
                    and pricelist_item.base_pricelist_id.discount_policy
                    == "without_discount"
                ):
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(
                        uom=uom.id
                    ).get_product_price_rule(
                        product, qty, self.folio_id.partner_id
                    )
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == "standard_price":
                field_name = "standard_price"
            if (
                pricelist_item.base == "pricelist"
                and pricelist_item.base_pricelist_id
            ):
                field_name = "price"
                product = product.with_context(
                    pricelist=pricelist_item.base_pricelist_id.id
                )
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        product_currency = (
            product_currency
            or (product.company_id and product.company_id.currency_id)
            or self.env.user.company_id.currency_id
        )
        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(
                    product_currency, currency_id
                )

        product_uom = self.env.context.get("uom") or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0
        return product[field_name] * uom_factor * cur_factor, currency_id.id

    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        if self.folio_id.pricelist_id.discount_policy == "with_discount":
            return product.with_context(
                pricelist=self.folio_id.pricelist_id.id
            ).price
        product_context = dict(
            self.env.context,
            partner_id=self.folio_id.partner_id.id,
            date=self.folio_id.date_order,
            uom=self.product_uom.id,
        )
        final_price, rule_id = self.folio_id.pricelist_id.with_context(
            product_context
        ).get_product_price_rule(
            self.product_id,
            self.product_uom_qty or 1.0,
            self.folio_id.partner_id,
        )
        base_price, currency_id = self.with_context(
            product_context
        )._get_real_price_currency(
            product,
            rule_id,
            self.product_uom_qty,
            self.product_uom,
            self.folio_id.pricelist_id.id,
        )
        if currency_id != self.folio_id.pricelist_id.currency_id.id:
            base_price = (
                self.env["res.currency"]
                .browse(currency_id)
                .with_context(product_context)
                .compute(base_price, self.folio_id.pricelist_id.currency_id)
            )
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    def _compute_tax_id(self):
        for line in self:
            fpos = (
                line.folio_id.fiscal_position_id
                or line.folio_id.partner_id.property_account_position_id
            )
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(
                lambda r: not line.company_id
                or r.company_id == line.company_id
            )
            line.tax_id = (
                fpos.map_tax(
                    taxes, line.product_id, line.folio_id.partner_shipping_id
                )
                if fpos
                else taxes
            )

    @api.onchange("product_id")
    def product_id_change(self):
        """
 -        @param self: object pointer
 -        """
        if not self.product_id:
            return {"domain": {"product_uom": []}}
        vals = {}
        domain = {
            "product_uom": [
                ("category_id", "=", self.product_id.uom_id.category_id.id)
            ]
        }
        if not self.product_uom or (
            self.product_id.uom_id.id != self.product_uom.id
        ):
            vals["product_uom"] = self.product_id.uom_id
        product = self.product_id.with_context(
            lang=self.folio_id.partner_id.lang,
            partner=self.folio_id.partner_id.id,
            quantity=vals.get("product_uom_qty") or self.product_uom_qty,
            date=self.folio_id.date_order,
            pricelist=self.folio_id.pricelist_id.id,
            uom=self.product_uom.id,
        )

        result = {"domain": domain}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != "no-message":
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning["title"] = title
            warning["message"] = message
            result = {"warning": warning}
            if product.sale_line_warn == "block":
                self.product_id = False
                return result

        name = product.name_get()[0][1]
        if product.description_sale:
            name += "\n" + product.description_sale
        vals["name"] = name

        self._compute_tax_id()

        if self.folio_id.pricelist_id and self.folio_id.partner_id:
            vals["price_unit"] = self.env[
                "account.tax"
            ]._fix_tax_included_price_company(
                self._get_display_price(product),
                product.taxes_id,
                self.tax_id,
                self.company_id,
            )
        self.update(vals)
        return result

    @api.onchange("checkin_date", "checkout_date")
    def _onchange_checkout_dates(self):
        """
        When you change checkin_date or checkout_date it will checked it
        and update the qty of hotel folio line
        -----------------------------------------------------------------
        @param self: object pointer
        """

        configured_addition_hours = (
            self.folio_id.warehouse_id.company_id.additional_hours
        )
        myduration = 0
        if self.checkin_date and self.checkout_date:
            dur = self.checkout_date - self.checkin_date
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
        avail_prod_ids = []
        for room in hotel_room_obj.search([]):
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

    def button_confirm(self):
        """
        @param self: object pointer
        """
        for folio in self:
            line = folio.order_line_id
            line.button_confirm()
        return True

    def button_done(self):
        """
        @param self: object pointer
        """
        for rec in self:
            lines = [folio_line.order_line_id for folio_line in rec]
            lines.button_done()
            rec.write({"state": "done"})
        return True

    def copy_data(self, default=None):
        """
        @param self: object pointer
        @param default: dict of default values to be set
        """

        sale_line_obj = self.order_line_id
        return sale_line_obj.copy_data(default=default)
