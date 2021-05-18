# See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt


class HotelFolio(models.Model):

    _inherit = "hotel.folio"
    _order = "reservation_id desc"

    reservation_id = fields.Many2one(
        "hotel.reservation", "Reservation", ondelete="restrict"
    )

    def write(self, vals):
        context = dict(self._context)
        context.update({"from_reservation": True})
        res = super(HotelFolio, self).write(vals)
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        for folio in self:
            reservations = reservation_line_obj.search(
                [("reservation_id", "=", folio.reservation_id.id)]
            )
            if len(reservations) == 1:
                for line in folio.reservation_id.reservation_line:
                    for room in line.reserve:
                        vals = {
                            "room_id": room.id,
                            "check_in": folio.checkin_date,
                            "check_out": folio.checkout_date,
                            "state": "assigned",
                            "reservation_id": folio.reservation_id.id,
                        }
                        reservations.write(vals)
        return res


class HotelFolioLineExt(models.Model):

    _inherit = "hotel.folio.line"

    @api.onchange("checkin_date", "checkout_date")
    def on_change_checkout(self):
        res = super(HotelFolioLineExt, self).on_change_checkout()
        avail_prod_ids = []
        hotel_room_ids = self.env["hotel.room"].search([])
        for room in hotel_room_ids:
            assigned = False
            for line in room.room_reservation_line_ids:
                if line.status != "cancel":
                    if (self.checkin_date <= line.check_in <= self.checkout_date) or (
                        self.checkin_date <= line.check_out <= self.checkout_date
                    ):
                        assigned = True
                    elif (line.check_in <= self.checkin_date <= line.check_out) or (
                        line.check_in <= self.checkout_date <= line.check_out
                    ):
                        assigned = True
            if not assigned:
                avail_prod_ids.append(room.product_id.id)
        return res

    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        Update Hotel Room Reservation line history"""
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        room_obj = self.env["hotel.room"]
        prod_id = vals.get("product_id") or self.product_id.id
        chkin = vals.get("checkin_date") or self.checkin_date
        chkout = vals.get("checkout_date") or self.checkout_date
        is_reserved = self.is_reserved
        if prod_id and is_reserved:
            prod_room = room_obj.search([("product_id", "=", prod_id)], limit=1)
            if self.product_id and self.checkin_date and self.checkout_date:
                old_prod_room = room_obj.search(
                    [("product_id", "=", self.product_id.id)], limit=1
                )
                if prod_room and old_prod_room:
                    # Check for existing room lines.
                    rm_lines = reservation_line_obj.search(
                        [
                            ("room_id", "=", old_prod_room.id),
                            ("check_in", "=", self.checkin_date),
                            ("check_out", "=", self.checkout_date),
                        ]
                    )
                    if rm_lines:
                        rm_line_vals = {
                            "room_id": prod_room.id,
                            "check_in": chkin,
                            "check_out": chkout,
                        }
                        rm_lines.write(rm_line_vals)
        return super(HotelFolioLineExt, self).write(vals)


class HotelReservation(models.Model):

    _name = "hotel.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = "reservation_no desc"
    _inherit = ["mail.thread"]

    def _compute_folio_id(self):
        for res in self:
            res.update({"no_of_folio": len(res.folio_id.ids)})

    reservation_no = fields.Char("Reservation No", readonly=True)
    date_order = fields.Datetime(
        "Date Ordered",
        readonly=True,
        required=True,
        index=True,
        default=lambda self: fields.Datetime.now(),
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
    )
    pricelist_id = fields.Many2one(
        "product.pricelist",
        "Scheme",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Pricelist for current reservation.",
    )
    partner_invoice_id = fields.Many2one(
        "res.partner",
        "Invoice Address",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Invoice address for " "current reservation.",
    )
    partner_order_id = fields.Many2one(
        "res.partner",
        "Ordering Contact",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="The name and address of the "
        "contact that requested the order "
        "or quotation.",
    )
    partner_shipping_id = fields.Many2one(
        "res.partner",
        "Delivery Address",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Delivery address" "for current reservation. ",
    )
    checkin = fields.Datetime(
        "Expected-Date-Arrival",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    checkout = fields.Datetime(
        "Expected-Date-Departure",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    adults = fields.Integer(
        "Adults",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="List of adults there in guest list. ",
    )
    children = fields.Integer(
        "Children",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Number of children there in guest list.",
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
    )
    folio_id = fields.Many2many(
        "hotel.folio",
        "hotel_folio_reservation_rel",
        "order_id",
        "invoice_id",
        string="Folio",
    )
    no_of_folio = fields.Integer("No. Folio", compute="_compute_folio_id")

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        for reserv_rec in self:
            if reserv_rec.state != "draft":
                raise ValidationError(
                    _("Sorry, you can only delete the reservation when it's draft!")
                )
        return super(HotelReservation, self).unlink()

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
                    raise ValidationError(_("Please Select Rooms For Reservation."))
                cap = sum(room.capacity for room in rec.reserve)
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
                        """Check-in date should be greater than """
                        """the current date."""
                    )
                )
            if self.checkout < self.checkin:
                raise ValidationError(
                    _("""Check-out date should be greater """ """than Check-in date.""")
                )

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        if not self.partner_id:
            self.update(
                {
                    "partner_invoice_id": False,
                    "partner_shipping_id": False,
                    "partner_order_id": False,
                }
            )
        else:
            addr = self.partner_id.address_get(["delivery", "invoice", "contact"])
            self.update(
                {
                    "partner_invoice_id": addr["invoice"],
                    "partner_shipping_id": addr["delivery"],
                    "partner_order_id": addr["contact"],
                    "pricelist_id": self.partner_id.property_product_pricelist.id,
                }
            )

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        vals["reservation_no"] = (
            self.env["ir.sequence"].next_by_code("hotel.reservation") or "New"
        )
        return super(HotelReservation, self).create(vals)

    def check_overlap(self, date1, date2):
        delta = date2 - date1
        return {date1 + timedelta(days=i) for i in range(delta.days + 1)}

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
            reserv_checkin = reservation.checkin
            reserv_checkout = reservation.checkout
            room_bool = False
            for line_id in reservation.reservation_line:
                for room in line_id.reserve:
                    if room.room_reservation_line_ids:
                        for reserv in room.room_reservation_line_ids.search(
                            [
                                ("status", "in", ("confirm", "done")),
                                ("room_id", "=", room.id),
                            ]
                        ):
                            check_in = reserv.check_in
                            check_out = reserv.check_out
                            if check_in <= reserv_checkin <= check_out:
                                room_bool = True
                            if check_in <= reserv_checkout <= check_out:
                                room_bool = True
                            if (
                                reserv_checkin <= check_in
                                and reserv_checkout >= check_out
                            ):
                                room_bool = True
                            r_checkin = (reservation.checkin).date()
                            r_checkout = (reservation.checkout).date()
                            check_intm = (reserv.check_in).date()
                            check_outtm = (reserv.check_out).date()
                            range1 = [r_checkin, r_checkout]
                            range2 = [check_intm, check_outtm]
                            overlap_dates = self.check_overlap(
                                *range1
                            ) & self.check_overlap(*range2)
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
                                    "room_id": room.id,
                                    "check_in": reservation.checkin,
                                    "check_out": reservation.checkout,
                                    "state": "assigned",
                                    "reservation_id": reservation.id,
                                }
                                room.write({"isroom": False, "status": "occupied"})
                        else:
                            self.state = "confirm"
                            vals = {
                                "room_id": room.id,
                                "check_in": reservation.checkin,
                                "check_out": reservation.checkout,
                                "state": "assigned",
                                "reservation_id": reservation.id,
                            }
                            room.write({"isroom": False, "status": "occupied"})
                    else:
                        self.state = "confirm"
                        vals = {
                            "room_id": room.id,
                            "check_in": reservation.checkin,
                            "check_out": reservation.checkout,
                            "state": "assigned",
                            "reservation_id": reservation.id,
                        }
                        room.write({"isroom": False, "status": "occupied"})
                    reservation_line_obj.create(vals)
        return True

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
        reservation_lines = hotel_res_line_obj.search([("line_id", "in", self.ids)])
        for reservation_line in reservation_lines:
            reservation_line.reserve.write({"isroom": True, "status": "available"})
        return True

    def set_to_draft_reservation(self):
        self.update({"state": "draft"})

    def action_send_reservation_mail(self):
        """
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        """
        self.ensure_one(), "This is for a single id at a time."
        template_id = self.env.ref(
            "hotel_reservation.email_template_hotel_reservation"
        ).id
        compose_form_id = self.env.ref("mail.email_compose_message_wizard_form").id
        ctx = {
            "default_model": "hotel.reservation",
            "default_res_id": self.id,
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment",
            "force_send": True,
            "mark_so_as_sent": True,
        }
        return {
            "type": "ir.actions.act_window",
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
        now_date = fields.Date.today()
        template_id = self.env.ref(
            "hotel_reservation.mail_template_reservation_reminder_24hrs"
        )
        for reserv_rec in self:
            checkin_date = reserv_rec.checkin
            difference = relativedelta(now_date, checkin_date)
            if (
                difference.days == -1
                and reserv_rec.partner_id.email
                and reserv_rec.state == "confirm"
            ):
                template_id.send_mail(reserv_rec.id, force_send=True)
        return True

    def create_folio(self):
        """
        This method is for create new hotel folio.
        -----------------------------------------
        @param self: The object pointer
        @return: new record set for hotel folio.
        """
        hotel_folio_obj = self.env["hotel.folio"]
        for reservation in self:
            folio_lines = []
            checkin_date = reservation["checkin"]
            checkout_date = reservation["checkout"]
            duration_vals = self._onchange_check_dates(
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
                    r.write({"status": "occupied", "isroom": False})
            folio_vals.update({"room_line_ids": folio_lines})
            folio = hotel_folio_obj.create(folio_vals)
            for rm_line in folio.room_line_ids:
                rm_line.product_id_change()
            self.write({"folio_id": [(6, 0, folio.ids)], "state": "done"})
        return True

    def _onchange_check_dates(
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
        configured_addition_hours = self.warehouse_id.company_id.additional_hours
        duration = 0
        if checkin_date and checkout_date:
            dur = checkout_date - checkin_date
            duration = dur.days + 1
            if configured_addition_hours > 0:
                additional_hours = abs(dur.seconds / 60)
                if additional_hours <= abs(configured_addition_hours * 60):
                    duration -= 1
        value.update({"duration": duration})
        return value

    def open_folio_view(self):
        folios = self.mapped("folio_id")
        action = self.env.ref("hotel.open_hotel_folio1_form_tree_all").read()[0]
        if len(folios) > 1:
            action["domain"] = [("id", "in", folios.ids)]
        elif len(folios) == 1:
            action["views"] = [(self.env.ref("hotel.view_hotel_folio_form").id, "form")]
            action["res_id"] = folios.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action


class HotelReservationLine(models.Model):

    _name = "hotel_reservation.line"
    _description = "Reservation Line"

    name = fields.Char("Name")
    line_id = fields.Many2one("hotel.reservation")
    reserve = fields.Many2many(
        "hotel.room",
        "hotel_reservation_line_room_rel",
        "hotel_reservation_line_id",
        "room_id",
        domain="[('isroom','=',True),\
                               ('categ_id','=',categ_id)]",
    )
    categ_id = fields.Many2one("hotel.room.type", "Room Type")

    @api.onchange("categ_id")
    def on_change_categ(self):
        """
        When you change categ_id it check checkin and checkout are
        filled or not if not then raise warning
        -----------------------------------------------------------
        @param self: object pointer
        """
        if not self.line_id.checkin:
            raise ValidationError(
                _(
                    """Before choosing a room,\n You have to """
                    """select a Check in date or a Check out """
                    """ date in the reservation form."""
                )
            )
        hotel_room_ids = self.env["hotel.room"].search(
            [("room_categ_id", "=", self.categ_id.id)]
        )
        room_ids = []
        for room in hotel_room_ids:
            assigned = False
            for line in room.room_reservation_line_ids:
                if line.status != "cancel":
                    if (
                        self.line_id.checkin <= line.check_in <= self.line_id.checkout
                    ) or (
                        self.line_id.checkin <= line.check_out <= self.line_id.checkout
                    ):
                        assigned = True
                    elif (line.check_in <= self.line_id.checkin <= line.check_out) or (
                        line.check_in <= self.line_id.checkout <= line.check_out
                    ):
                        assigned = True
            for rm_line in room.room_line_ids:
                if rm_line.status != "cancel":
                    if (
                        self.line_id.checkin
                        <= rm_line.check_in
                        <= self.line_id.checkout
                    ) or (
                        self.line_id.checkin
                        <= rm_line.check_out
                        <= self.line_id.checkout
                    ):
                        assigned = True
                    elif (
                        rm_line.check_in <= self.line_id.checkin <= rm_line.check_out
                    ) or (
                        rm_line.check_in <= self.line_id.checkout <= rm_line.check_out
                    ):
                        assigned = True
            if not assigned:
                room_ids.append(room.id)
        domain = {"reserve": [("id", "in", room_ids)]}
        return {"domain": domain}

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        hotel_room_reserv_line_obj = self.env["hotel.room.reservation.line"]
        for reserv_rec in self:
            for rec in reserv_rec.reserve:
                myobj = hotel_room_reserv_line_obj.search(
                    [
                        ("room_id", "=", rec.id),
                        ("reservation_id", "=", reserv_rec.line_id.id),
                    ]
                )
                if myobj:
                    rec.write({"isroom": True, "status": "available"})
                    myobj.unlink()
        return super(HotelReservationLine, self).unlink()


class HotelRoomReservationLine(models.Model):

    _name = "hotel.room.reservation.line"
    _description = "Hotel Room Reservation"
    _rec_name = "room_id"

    room_id = fields.Many2one("hotel.room", string="Room id")
    check_in = fields.Datetime("Check In Date", required=True)
    check_out = fields.Datetime("Check Out Date", required=True)
    state = fields.Selection(
        [("assigned", "Assigned"), ("unassigned", "Unassigned")], "Room Status"
    )
    reservation_id = fields.Many2one("hotel.reservation", "Reservation")
    status = fields.Selection(string="state", related="reservation_id.state")


class HotelRoom(models.Model):

    _inherit = "hotel.room"
    _description = "Hotel Room"

    room_reservation_line_ids = fields.One2many(
        "hotel.room.reservation.line", "room_id", string="Room Reserve Line"
    )

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        for room in self:
            for reserv_line in room.room_reservation_line_ids:
                if reserv_line.status == "confirm":
                    raise ValidationError(
                        _(
                            "User is not able to delete the \
                                            room after the room in %s state \
                                            in reservation"
                        )
                        % (reserv_line.status)
                    )
        return super(HotelRoom, self).unlink()

    @api.model
    def cron_room_line(self):
        """
        This method is for scheduler
        every 1min scheduler will call this method and check Status of
        room is occupied or available
        --------------------------------------------------------------
        @param self: The object pointer
        @return: update status of hotel room reservation line
        """
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        folio_room_line_obj = self.env["folio.room.line"]
        now = datetime.now()
        curr_date = now.strftime(dt)
        for room in self.search([]):
            reserv_line_ids = [
                reservation_line.id
                for reservation_line in room.room_reservation_line_ids
            ]
            reservation_line_ids = reservation_line_obj.search(
                [
                    ("id", "in", reserv_line_ids),
                    ("check_in", "<=", curr_date),
                    ("check_out", ">=", curr_date),
                ]
            )
            rooms_ids = [room_line.id for room_line in room.room_line_ids]
            room_line_ids = folio_room_line_obj.search(
                [
                    ("id", "in", rooms_ids),
                    ("check_in", "<=", curr_date),
                    ("check_out", ">=", curr_date),
                ]
            )
            status = {"isroom": True, "color": 5}
            if reservation_line_ids:
                status = {"isroom": False, "color": 2}
            room.write(status)
            if room_line_ids:
                status = {"isroom": False, "color": 2}
            room.write(status)
            if reservation_line_ids and room_line_ids:
                raise ValidationError(
                    _("Please Check Rooms Status for %s.") % room.name
                )
        return True


class RoomReservationSummary(models.Model):

    _name = "room.reservation.summary"
    _description = "Room reservation summary"

    name = fields.Char(
        "Reservation Summary", default="Reservations Summary", invisible=True
    )
    date_from = fields.Datetime("Date From", default=lambda self: fields.Date.today())
    date_to = fields.Datetime(
        "Date To",
        default=lambda self: fields.Date.today() + relativedelta(days=30),
    )
    summary_header = fields.Text("Summary Header")
    room_summary = fields.Text("Room Summary")

    def room_reservation(self):
        """
        @param self: object pointer
        """
        resource_id = self.env.ref("hotel_reservation.view_hotel_reservation_form").id
        return {
            "name": _("Reconcile Write-Off"),
            "context": self._context,
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hotel.reservation",
            "views": [(resource_id, "form")],
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.onchange("date_from", "date_to")  # noqa C901 (function is too complex)
    def get_room_summary(self):  # noqa C901 (function is too complex)
        """
        @param self: object pointer
        """
        res = {}
        all_detail = []
        room_obj = self.env["hotel.room"]
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        folio_room_line_obj = self.env["folio.room.line"]
        user_obj = self.env["res.users"]
        date_range_list = []
        main_header = []
        summary_header_list = ["Rooms"]
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise UserError(
                    _(
                        "Please Check Time period Date From can't \
                                   be greater than Date To !"
                    )
                )
            if self._context.get("tz", False):
                timezone = pytz.timezone(self._context.get("tz", False))
            else:
                timezone = pytz.timezone("UTC")
            d_frm_obj = (
                (self.date_from)
                .replace(tzinfo=pytz.timezone("UTC"))
                .astimezone(timezone)
            )
            d_to_obj = (
                (self.date_to).replace(tzinfo=pytz.timezone("UTC")).astimezone(timezone)
            )
            temp_date = d_frm_obj
            while temp_date <= d_to_obj:
                val = ""
                val = (
                    str(temp_date.strftime("%a"))
                    + " "
                    + str(temp_date.strftime("%b"))
                    + " "
                    + str(temp_date.strftime("%d"))
                )
                summary_header_list.append(val)
                date_range_list.append(temp_date.strftime(dt))
                temp_date = temp_date + timedelta(days=1)
            all_detail.append(summary_header_list)
            room_ids = room_obj.search([])
            all_room_detail = []
            for room in room_ids:
                room_detail = {}
                room_list_stats = []
                room_detail.update({"name": room.name or ""})
                if not room.room_reservation_line_ids and not room.room_line_ids:
                    for chk_date in date_range_list:
                        room_list_stats.append(
                            {
                                "state": "Free",
                                "date": chk_date,
                                "room_id": room.id,
                            }
                        )
                else:
                    for chk_date in date_range_list:
                        ch_dt = chk_date[:10] + " 23:59:59"
                        ttime = datetime.strptime(ch_dt, dt)
                        c = ttime.replace(tzinfo=timezone).astimezone(
                            pytz.timezone("UTC")
                        )
                        chk_date = c.strftime(dt)
                        reserline_ids = room.room_reservation_line_ids.ids
                        reservline_ids = reservation_line_obj.search(
                            [
                                ("id", "in", reserline_ids),
                                ("check_in", "<=", chk_date),
                                ("check_out", ">=", chk_date),
                                ("state", "=", "assigned"),
                            ]
                        )
                        if not reservline_ids:
                            sdt = dt
                            chk_date = datetime.strptime(chk_date, sdt)
                            chk_date = datetime.strftime(
                                chk_date - timedelta(days=1), sdt
                            )
                            reservline_ids = reservation_line_obj.search(
                                [
                                    ("id", "in", reserline_ids),
                                    ("check_in", "<=", chk_date),
                                    ("check_out", ">=", chk_date),
                                    ("state", "=", "assigned"),
                                ]
                            )
                            for res_room in reservline_ids:
                                cid = res_room.check_in
                                cod = res_room.check_out
                                dur = cod - cid
                                if room_list_stats:
                                    count = 0
                                    for rlist in room_list_stats:
                                        cidst = datetime.strftime(cid, dt)
                                        codst = datetime.strftime(cod, dt)
                                        rm_id = res_room.room_id.id
                                        ci = rlist.get("date") >= cidst
                                        co = rlist.get("date") <= codst
                                        rm = rlist.get("room_id") == rm_id
                                        st = rlist.get("state") == "Reserved"
                                        if ci and co and rm and st:
                                            count += 1
                                    if count - dur.days == 0:
                                        c_id1 = user_obj.browse(self._uid)
                                        c_id = c_id1.company_id
                                        con_add = 0
                                        amin = 0.0
                                        # When configured_addition_hours is
                                        # greater than zero then we calculate
                                        # additional minutes
                                        if c_id:
                                            con_add = c_id.additional_hours
                                        if con_add > 0:
                                            amin = abs(con_add * 60)
                                        hr_dur = abs(dur.seconds / 60)
                                        if amin > 0:
                                            # When additional minutes is greater
                                            # than zero then check duration with
                                            # extra minutes and give the room
                                            # reservation status is reserved
                                            # --------------------------
                                            if hr_dur >= amin:
                                                reservline_ids = True
                                            else:
                                                reservline_ids = False
                                        else:
                                            if hr_dur > 0:
                                                reservline_ids = True
                                            else:
                                                reservline_ids = False
                                    else:
                                        reservline_ids = False
                        fol_room_line_ids = room.room_line_ids.ids
                        chk_state = ["draft", "cancel"]
                        folio_resrv_ids = folio_room_line_obj.search(
                            [
                                ("id", "in", fol_room_line_ids),
                                ("check_in", "<=", chk_date),
                                ("check_out", ">=", chk_date),
                                ("status", "not in", chk_state),
                            ]
                        )
                        if reservline_ids or folio_resrv_ids:
                            room_list_stats.append(
                                {
                                    "state": "Reserved",
                                    "date": chk_date,
                                    "room_id": room.id,
                                    "is_draft": "No",
                                    "data_model": "",
                                    "data_id": 0,
                                }
                            )
                        else:
                            room_list_stats.append(
                                {
                                    "state": "Free",
                                    "date": chk_date,
                                    "room_id": room.id,
                                }
                            )

                room_detail.update({"value": room_list_stats})
                all_room_detail.append(room_detail)
            main_header.append({"header": summary_header_list})
            self.summary_header = str(main_header)
            self.room_summary = str(all_room_detail)
        return res


class QuickRoomReservation(models.TransientModel):
    _name = "quick.room.reservation"
    _description = "Quick Room Reservation"

    partner_id = fields.Many2one("res.partner", "Customer", required=True)
    check_in = fields.Datetime("Check In", required=True)
    check_out = fields.Datetime("Check Out", required=True)
    room_id = fields.Many2one("hotel.room", "Room", required=True)
    warehouse_id = fields.Many2one("stock.warehouse", "Hotel", required=True)
    pricelist_id = fields.Many2one("product.pricelist", "pricelist")
    partner_invoice_id = fields.Many2one(
        "res.partner", "Invoice Address", required=True
    )
    partner_order_id = fields.Many2one("res.partner", "Ordering Contact", required=True)
    partner_shipping_id = fields.Many2one(
        "res.partner", "Delivery Address", required=True
    )
    adults = fields.Integer("Adults")

    @api.onchange("check_out", "check_in")
    def on_change_check_out(self):
        """
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        if self.check_out and self.check_in:
            if self.check_out < self.check_in:
                raise ValidationError(
                    _(
                        "Checkout date should be greater \
                                         than Checkin date."
                    )
                )

    @api.onchange("partner_id")
    def onchange_partner_id_res(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        if not self.partner_id:
            self.update(
                {
                    "partner_invoice_id": False,
                    "partner_shipping_id": False,
                    "partner_order_id": False,
                }
            )
        else:
            addr = self.partner_id.address_get(["delivery", "invoice", "contact"])
            self.update(
                {
                    "partner_invoice_id": addr["invoice"],
                    "partner_shipping_id": addr["delivery"],
                    "partner_order_id": addr["contact"],
                    "pricelist_id": self.partner_id.property_product_pricelist.id,
                }
            )

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        res = super(QuickRoomReservation, self).default_get(fields)
        if self._context:
            keys = self._context.keys()
            if "date" in keys:
                res.update({"check_in": self._context["date"]})
            if "room_id" in keys:
                roomid = self._context["room_id"]
                res.update({"room_id": int(roomid)})
        return res

    def room_reserve(self):
        """
        This method create a new record for hotel.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel reservation.
        """
        hotel_res_obj = self.env["hotel.reservation"]
        for res in self:
            rec = hotel_res_obj.create(
                {
                    "partner_id": res.partner_id.id,
                    "partner_invoice_id": res.partner_invoice_id.id,
                    "partner_order_id": res.partner_order_id.id,
                    "partner_shipping_id": res.partner_shipping_id.id,
                    "checkin": res.check_in,
                    "checkout": res.check_out,
                    "warehouse_id": res.warehouse_id.id,
                    "pricelist_id": res.pricelist_id.id,
                    "adults": res.adults,
                    "reservation_line": [
                        (
                            0,
                            0,
                            {
                                "reserve": [(6, 0, [res.room_id.id])],
                                "name": (res.room_id and res.room_id.name or ""),
                            },
                        )
                    ],
                }
            )
        return rec
