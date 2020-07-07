# See LICENSE file for full copyright and licensing details.

import datetime
import time

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
            # dt_value needs to be a datetime.datetime object\
            # (so notime.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.datetime.strptime(src_tstamp_str, src_format)
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
    folio_id = fields.Many2one("hotel.folio", string="Folio Number")
    status = fields.Selection(string="state", related="folio_id.state")


class HotelFolio(models.Model):
    @api.multi
    def name_get(self):
        res = []
        disp = ""
        for rec in self:
            if rec.order_id:
                disp = str(rec.name)
                res.append((rec.id, disp))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        args += [("name", operator, name)]
        mids = self.search(args, limit=100)
        return mids.name_get()

    @api.model
    def _needaction_count(self, domain=None):
        """
         Show a count of draft state folio on the menu badge.
         @param self: object pointer
        """
        return self.search_count([("state", "=", "draft")])

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
        tm_delta = datetime.timedelta(days=1)
        return (
            datetime.datetime.strptime(
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

    @api.multi
    def copy(self, default=None):
        """
        @param self: object pointer
        @param default: dict of default values to be set
        """
        return super(HotelFolio, self).copy(default=default)

    _name = "hotel.folio"
    _description = "hotel folio new"
    _rec_name = "order_id"
    _order = "id"

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
    room_lines = fields.One2many(
        "hotel.folio.line",
        "folio_id",
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        help="Hotel room reservation detail.",
    )
    service_lines = fields.One2many(
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
    hotel_invoice_id = fields.Many2one(
        "account.invoice", "Invoice", copy=False
    )
    duration_dummy = fields.Float("Duration Dummy")

    @api.constrains("room_lines")
    def folio_room_lines(self):
        """
        This method is used to validate the room_lines.
        ------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        folio_rooms = []
        for room in self[0].room_lines:
            if room.product_id.id in folio_rooms:
                raise ValidationError(_("You Cannot Take Same Room Twice"))
            folio_rooms.append(room.product_id.id)

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
        configured_addition_hours = 0
        wid = self.warehouse_id
        whouse_com_id = wid or wid.company_id
        if whouse_com_id:
            configured_addition_hours = wid.company_id.additional_hours
        myduration = 0
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
            # To calculate additional hours in hotel room as per minutes
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    myduration += 1
        self.duration = myduration
        self.duration_dummy = self.duration

    @api.model
    def create(self, vals, check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio.
        """
        if not "service_lines" and "folio_id" in vals:
            tmp_room_lines = vals.get("room_lines", [])
            vals["order_policy"] = vals.get("hotel_policy", "manual")
            vals.update({"room_lines": []})
            folio_id = super(HotelFolio, self).create(vals)
            for line in tmp_room_lines:
                line[2].update({"folio_id": folio_id})
            vals.update({"room_lines": tmp_room_lines})
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
                        for room_rec in rec.room_lines:
                            prod = room_rec.product_id.name
                            room_obj = h_room_obj.search([("name", "=", prod)])
                            room_obj.write({"isroom": False})
                            vals = {
                                "room_id": room_obj.id,
                                "check_in": rec.checkin_date,
                                "check_out": rec.checkout_date,
                                "folio_id": rec.id,
                            }
                            folio_room_line_obj.create(vals)
            except Exception:
                for rec in folio_id:
                    for room_rec in rec.room_lines:
                        prod = room_rec.product_id.name
                        room_obj = h_room_obj.search([("name", "=", prod)])
                        room_obj.write({"isroom": False})
                        vals = {
                            "room_id": room_obj.id,
                            "check_in": rec.checkin_date,
                            "check_out": rec.checkout_date,
                            "folio_id": rec.id,
                        }
                        folio_room_line_obj.create(vals)
        return folio_id

    @api.multi
    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        product_obj = self.env["product.product"]
        h_room_obj = self.env["hotel.room"]
        folio_room_line_obj = self.env["folio.room.line"]
        room_lst = []
        room_lst1 = []
        for rec in self:
            for res in rec.room_lines:
                room_lst1.append(res.product_id.id)
            if vals and vals.get("duration_dummy", False):
                vals["duration"] = vals.get("duration_dummy", 0.0)
            else:
                vals["duration"] = rec.duration
            for folio_rec in rec.room_lines:
                room_lst.append(folio_rec.product_id.id)
            new_rooms = set(room_lst).difference(set(room_lst1))
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
            if len(list(new_rooms)) == 0:
                room_list_obj = product_obj.browse(room_lst1)
                for rom in room_list_obj:
                    room_obj = h_room_obj.search([("name", "=", rom.name)])
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

    @api.onchange("warehouse_id")
    def onchange_warehouse_id(self):
        """
        When you change warehouse it will update the warehouse of
        the hotel folio as well
        ----------------------------------------------------------
        @param self: object pointer
        """
        return self.order_id._onchange_warehouse_id()

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel folio as well
        ---------------------------------------------------------------
        @param self: object pointer
        """
        if self.partner_id:
            partner_rec = self.env["res.partner"].browse(self.partner_id.id)
            order_ids = [folio.order_id.id for folio in self]
            if not order_ids:
                self.partner_invoice_id = partner_rec.id
                self.partner_shipping_id = partner_rec.id
                self.pricelist_id = partner_rec.property_product_pricelist.id
                raise (_("Not Any Order For  %s ") % (partner_rec.name))
            else:
                self.partner_invoice_id = partner_rec.id
                self.partner_shipping_id = partner_rec.id
                self.pricelist_id = partner_rec.property_product_pricelist.id

    @api.multi
    def action_done(self):
        self.state = "done"

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        @param self: object pointer
        """
        # fixme does not seem to go through here
        room_lst = []
        invoice_id = self.order_id.action_invoice_create(
            grouped=False, final=False
        )
        for line in self:
            values = {"invoiced": True, "hotel_invoice_id": invoice_id}
            line.write(values)
            for rec in line.room_lines:
                room_lst.append(rec.product_id)
            for room in room_lst:
                room_rec = self.env["hotel.room"].search(
                    [("name", "=", room.name)]
                )
                room_rec.write({"isroom": True})
        return invoice_id

    @api.multi
    def action_invoice_cancel(self):
        """
        @param self: object pointer
        """
        if not self.order_id:
            raise UserError(_("Order id is not available"))
        for sale in self:
            for line in sale.order_line:
                line.write({"invoiced": "invoiced"})
        self.state = "invoice_except"
        return self.order_id.action_invoice_cancel

    @api.multi
    def action_cancel(self):
        """
        @param self: object pointer
        """
        if not self.order_id:
            raise UserError(_("Order id is not available"))
        for sale in self:
            for invoice in sale.invoice_ids:
                invoice.state = "cancel"
        return self.order_id.action_cancel()

    @api.multi
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

    @api.multi
    def test_state(self, mode):
        """
        @param self: object pointer
        @param mode: state of workflow
        """
        write_done_ids = []
        write_cancel_ids = []
        if write_done_ids:
            test_obj = self.env["sale.order.line"].browse(write_done_ids)
            test_obj.write({"state": "done"})
        if write_cancel_ids:
            test_obj = self.env["sale.order.line"].browse(write_cancel_ids)
            test_obj.write({"state": "cancel"})

    @api.multi
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
        self.write({"state": "draft", "invoice_ids": [], "shipped": 0})
        sale_line_obj = self.env["sale.order.line"].browse(line_ids)
        sale_line_obj.write(
            {
                "invoiced": False,
                "state": "draft",
                "invoice_lines": [(6, 0, [])],
            }
        )
        return True
