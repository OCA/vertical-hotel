# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt


class HotelReservation(models.Model):
    _name = "hotel.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = "reservation_no desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    reservation_no = fields.Char("Reservation No", readonly=True)
    date_order = fields.Datetime(
        "Date Ordered",
        readonly=True,
        required=True,
        index=True,
        default=(lambda *a: time.strftime(dt)),
        track_visibility="onchange",
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        "Hotel",
        readonly=True,
        index=True,
        required=True,
        default=1,
        states={"draft": [("readonly", False)]},
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Guest Name",
        readonly=True,
        index=True,
        required=True,
        states={"draft": [("readonly", False)]},
        track_visibility="onchange",
    )
    pricelist_id = fields.Many2one(
        "product.pricelist",
        "Scheme",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Pricelist for current reservation.",
        track_visibility="onchange",
    )
    partner_invoice_id = fields.Many2one(
        "res.partner",
        "Invoice Address",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Invoice address for " "current reservation.",
        track_visibility="onchange",
    )
    partner_order_id = fields.Many2one(
        "res.partner",
        "Ordering Contact",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="The name and address of the "
        "contact that requested the order "
        "or quotation.",
        track_visibility="onchange",
    )
    partner_shipping_id = fields.Many2one(
        "res.partner",
        "Delivery Address",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Delivery address" "for current reservation. ",
        track_visibility="onchange",
    )
    checkin = fields.Datetime(
        "Expected-Date-Arrival",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        track_visibility="onchange",
    )
    checkout = fields.Datetime(
        "Expected-Date-Departure",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        track_visibility="onchange",
    )
    adults = fields.Integer(
        "Adults",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="List of adults there in guest list. ",
        track_visibility="onchange",
    )
    children = fields.Integer(
        "Children",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Number of children there in guest list.",
        track_visibility="onchange",
    )
    reservation_line = fields.One2many(
        "hotel_reservation.line",
        "line_id",
        "Reservation Line",
        help="Hotel room reservation details.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("cancel", "Cancel"),
            ("done", "Done"),
        ],
        "State",
        readonly=True,
        default=lambda *a: "draft",
        track_visibility="onchange",
    )
    folio_id = fields.Many2many(
        "hotel.folio",
        "hotel_folio_reservation_rel",
        "order_id",
        "invoice_id",
        string="Folio",
        track_visibility="onchange",
    )
    no_of_folio = fields.Integer("Folio", compute="_compute_folio_id")
    dummy = fields.Datetime("Dummy")
    open = fields.Boolean(
        string="Open Rooms",
        help="Should the rooms be opened for arriving guest.",
        track_visibility="onchange",
    )
    note = fields.Text(string="Note", track_visibility="onchange")

    @api.multi
    def _compute_folio_id(self):
        folio_list = []
        for res in self:
            for folio in res.folio_id:
                folio_list.append(folio.id)
            folio_len = len(folio_list)
            res.no_of_folio = folio_len
        return folio_len

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        for reserv_rec in self:
            if reserv_rec.state != "draft":
                raise ValidationError(
                    _(
                        "You cannot delete Reservation in %s\
                                         state."
                    )
                    % (reserv_rec.state)
                )
        return super(HotelReservation, self).unlink()

    @api.multi
    def copy(self):
        ctx = dict(self._context) or {}
        ctx.update({"duplicate": True})
        return super(HotelReservation, self.with_context(ctx)).copy()

    @api.constrains("reservation_line", "adults", "children")
    def check_reservation_rooms(self):
        """
        This method is used to validate the reservation_line.
        -----------------------------------------------------
        @param self: object pointer
        @return: raise a warning depending on the validation
        """
        ctx = dict(self._context) or {}
        for reservation in self:
            cap = 0
            for rec in reservation.reservation_line:
                if len(rec.reserve) == 0:
                    raise ValidationError(
                        _("Please Select Rooms For Reservation.")
                    )
                for room in rec.reserve:
                    cap += room.capacity
            if not ctx.get("duplicate"):
                if (reservation.adults + reservation.children) > cap:
                    raise ValidationError(
                        _(
                            "Room Capacity Exceeded \n"
                            " Please Select Rooms According to"
                            " Members Accomodation."
                        )
                    )
            if reservation.adults <= 0:
                raise ValidationError(_("Adults must be more than 0"))

    @api.constrains("checkin", "checkout")
    def check_in_out_dates(self):
        """
        When date_order is less then check-in date or
        Checkout date should be greater than the check-in date.
        """
        if self.checkout and self.checkin:
            if self.checkin < self.date_order:
                raise ValidationError(
                    _(
                        "Check-in date should be greater than \
                                         the current date."
                    )
                )
            if self.checkout < self.checkin:
                raise ValidationError(
                    _(
                        "Check-out date should be greater \
                                         than Check-in date."
                    )
                )

    @api.model
    def _needaction_count(self, domain=None):
        """
         Show a count of draft state reservations on the menu badge.
         """
        return self.search_count([("state", "=", "draft")])

    @api.onchange("checkout", "checkin")
    def on_change_checkout(self):
        """
        When you change checkout or checkin update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        checkout_date = time.strftime(dt)
        checkin_date = time.strftime(dt)
        if not (checkout_date and checkin_date):
            return {"value": {}}
        delta = timedelta(days=1)
        dat_a = time.strptime(checkout_date, dt)[:5]
        addDays = datetime(*dat_a) + delta
        self.dummy = addDays.strftime(dt)

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        if not self.partner_id:
            self.partner_invoice_id = False
            self.partner_shipping_id = False
            self.partner_order_id = False
        else:
            addr = self.partner_id.address_get(
                ["delivery", "invoice", "contact"]
            )
            self.partner_invoice_id = addr["invoice"]
            self.partner_order_id = addr["contact"]
            self.partner_shipping_id = addr["delivery"]
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        vals["reservation_no"] = (
            self.env["ir.sequence"].next_by_code("hotel.reservation") or "New"
        )
        return super(HotelReservation, self).create(vals)

    @api.multi
    def check_overlap(self, date1, date2):
        date2 = datetime.strptime(date2, "%Y-%m-%d")
        date1 = datetime.strptime(date1, "%Y-%m-%d")
        delta = date2 - date1
        return {date1 + timedelta(days=i) for i in range(delta.days + 1)}

    @api.multi
    def confirmed_reservation(self):
        """
        This method create a new record set for hotel room reservation line
        -------------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel room reservation line.
        """
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        vals = {}
        for reservation in self:
            reserv_checkin = datetime.strptime(reservation.checkin, dt)
            reserv_checkout = datetime.strptime(reservation.checkout, dt)
            room_bool = False
            for line_id in reservation.reservation_line:
                for room_id in line_id.reserve:
                    if room_id.room_reservation_line_ids:
                        for reserv in room_id.room_reservation_line_ids.search(
                            [
                                ("status", "in", ("confirm", "done")),
                                ("room_id", "=", room_id.id),
                            ]
                        ):
                            check_in = datetime.strptime(reserv.check_in, dt)
                            check_out = datetime.strptime(reserv.check_out, dt)
                            if check_in <= reserv_checkin <= check_out:
                                room_bool = True
                            if check_in <= reserv_checkout <= check_out:
                                room_bool = True
                            if (
                                reserv_checkin <= check_in
                                and reserv_checkout >= check_out
                            ):
                                room_bool = True
                            mytime = "%Y-%m-%d"
                            r_checkin = datetime.strptime(
                                reservation.checkin, dt
                            ).date()
                            r_checkin = r_checkin.strftime(mytime)
                            r_checkout = datetime.strptime(
                                reservation.checkout, dt
                            ).date()
                            r_checkout = r_checkout.strftime(mytime)
                            check_intm = datetime.strptime(
                                reserv.check_in, dt
                            ).date()
                            check_outtm = datetime.strptime(
                                reserv.check_out, dt
                            ).date()
                            check_intm = check_intm.strftime(mytime)
                            check_outtm = check_outtm.strftime(mytime)
                            range1 = [r_checkin, r_checkout]
                            range2 = [check_intm, check_outtm]
                            overlap_dates = self.check_overlap(
                                *range1
                            ) & self.check_overlap(*range2)
                            overlap_dates = [
                                datetime.strftime(dates, "%d/%m/%Y")
                                for dates in overlap_dates
                            ]
                            if room_bool:
                                raise ValidationError(
                                    _(
                                        "You tried to Confirm "
                                        "Reservation with room"
                                        " those already "
                                        "reserved in this "
                                        "Reservation Period. "
                                        "Overlap Dates are "
                                        "%s"
                                    )
                                    % overlap_dates
                                )
                            else:
                                self.state = "confirm"
                                vals = {
                                    "room_id": room_id.id,
                                    "check_in": reservation.checkin,
                                    "check_out": reservation.checkout,
                                    "state": "assigned",
                                    "reservation_id": reservation.id,
                                }
                                room_id.write(
                                    {"isroom": False, "status": "occupied"}
                                )
                        else:
                            self.state = "confirm"
                            vals = {
                                "room_id": room_id.id,
                                "check_in": reservation.checkin,
                                "check_out": reservation.checkout,
                                "state": "assigned",
                                "reservation_id": reservation.id,
                            }
                            room_id.write(
                                {"isroom": False, "status": "occupied"}
                            )
                    else:
                        self.state = "confirm"
                        vals = {
                            "room_id": room_id.id,
                            "check_in": reservation.checkin,
                            "check_out": reservation.checkout,
                            "state": "assigned",
                            "reservation_id": reservation.id,
                        }
                        room_id.write({"isroom": False, "status": "occupied"})
                    reservation_line_obj.create(vals)
        return True

    @api.multi
    def cancel_reservation(self):
        """
        This method cancel record set for hotel room reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: cancel record set for hotel room reservation line.
        """
        room_res_line_obj = self.env["hotel.room.reservation.line"]
        hotel_res_line_obj = self.env["hotel_reservation.line"]
        self.state = "cancel"
        room_reservation_line = room_res_line_obj.search(
            [("reservation_id", "in", self.ids)]
        )
        room_reservation_line.write({"state": "unassigned"})
        room_reservation_line.unlink()
        reservation_lines = hotel_res_line_obj.search(
            [("line_id", "in", self.ids)]
        )
        for reservation_line in reservation_lines:
            reservation_line.reserve.write(
                {"isroom": True, "status": "available"}
            )
        return True

    @api.multi
    def set_to_draft_reservation(self):
        self.state = "draft"
        return True

    @api.multi
    def send_reservation_maill(self):
        """
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        """
        assert len(self._ids) == 1, "This is for a single id at a time."
        ir_model_data = self.env["ir.model.data"]
        try:
            template_id = ir_model_data.get_object_reference(
                "hotel_reservation", "mail_template_hotel_reservation"
            )[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                "mail", "email_compose_message_wizard_form"
            )[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update(
            {
                "default_model": "hotel.reservation",
                "default_res_id": self._ids[0],
                "default_use_template": bool(template_id),
                "default_template_id": template_id,
                "default_composition_mode": "comment",
                "force_send": True,
                "mark_so_as_sent": True,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form_id, "form")],
            "view_id": compose_form_id,
            "target": "new",
            "context": ctx,
            "force_send": True,
        }

    @api.model
    def reservation_reminder_24hrs(self):
        """
        This method is for scheduler
        every 1day scheduler will call this method to
        find all tomorrow's reservations.
        ----------------------------------------------
        @param self: The object pointer
        @return: send a mail
        """
        now_str = time.strftime(dt)
        now_date = datetime.strptime(now_str, dt)
        ir_model_data = self.env["ir.model.data"]
        template_id = ir_model_data.get_object_reference(
            "hotel_reservation", "mail_template_reservation_reminder_24hrs"
        )[1]
        template_rec = self.env["mail.template"].browse(template_id)
        for reserv_rec in self.search([]):
            checkin_date = datetime.strptime(reserv_rec.checkin, dt)
            difference = relativedelta(now_date, checkin_date)
            if (
                difference.days == -1
                and reserv_rec.partner_id.email
                and reserv_rec.state == "confirm"
            ):
                template_rec.send_mail(reserv_rec.id, force_send=True)
        return True

    @api.multi
    def create_folio(self):
        """
        This method is for create new hotel folio.
        -----------------------------------------
        @param self: The object pointer
        @return: new record set for hotel folio.
        """
        hotel_folio_obj = self.env["hotel.folio"]
        room_obj = self.env["hotel.room"]
        for reservation in self:
            folio_lines = []
            checkin_date = reservation["checkin"]
            checkout_date = reservation["checkout"]
            if not self.checkin < self.checkout:
                raise ValidationError(
                    _(
                        "Checkout date should be greater \
                                         than the Check-in date."
                    )
                )
            duration_vals = self.onchange_check_dates(
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                duration=False,
            )
            duration = duration_vals.get("duration") or 0.0
            folio_vals = {
                "date_order": reservation.date_order,
                "warehouse_id": reservation.warehouse_id.id,
                "partner_id": reservation.partner_id.id,
                "pricelist_id": reservation.pricelist_id.id,
                "partner_invoice_id": reservation.partner_invoice_id.id,
                "partner_shipping_id": reservation.partner_shipping_id.id,
                "checkin_date": reservation.checkin,
                "checkout_date": reservation.checkout,
                "duration": duration,
                "reservation_id": reservation.id,
                "service_lines": reservation["folio_id"],
            }
            for line in reservation.reservation_line:
                for r in line.reserve:
                    folio_lines.append(
                        (
                            0,
                            0,
                            {
                                "checkin_date": checkin_date,
                                "checkout_date": checkout_date,
                                "product_id": r.product_id and r.product_id.id,
                                "name": reservation["reservation_no"],
                                "price_unit": r.list_price,
                                "product_uom_qty": duration,
                                "is_reserved": True,
                            },
                        )
                    )
                    res_obj = room_obj.browse([r.id])
                    res_obj.write({"status": "occupied", "isroom": False})
            folio_vals.update({"room_lines": folio_lines})
            folio = hotel_folio_obj.create(folio_vals)
            if folio:
                for rm_line in folio.room_lines:
                    rm_line.product_id_change()
            self._cr.execute(
                "insert into hotel_folio_reservation_rel"
                "(order_id, invoice_id) values (%s,%s)",
                (reservation.id, folio.id),
            )
            self.state = "done"
        return True

    @api.multi
    def onchange_check_dates(
        self, checkin_date=False, checkout_date=False, duration=False
    ):
        """
        This method gives the duration between check in checkout if
        customer will leave only for some hour it would be considers
        as a whole day. If customer will checkin checkout for more or equal
        hours, which configured in company as additional hours than it would
        be consider as full days
        --------------------------------------------------------------------
        @param self: object pointer
        @return: Duration and checkout_date
        """
        value = {}
        configured_addition_hours = 0
        wc_id = self.warehouse_id
        whcomp_id = wc_id or wc_id.company_id
        if whcomp_id:
            configured_addition_hours = wc_id.company_id.additional_hours
        duration = 0
        if checkin_date and checkout_date:
            chkin_dt = datetime.strptime(checkin_date, dt)
            chkout_dt = datetime.strptime(checkout_date, dt)
            dur = chkout_dt - chkin_dt
            duration = dur.days + 1
            if configured_addition_hours > 0:
                additional_hours = abs(dur.seconds / 60)
                if additional_hours <= abs(configured_addition_hours * 60):
                    duration -= 1
        value.update({"duration": duration})
        return value
