# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HotelReservation(models.Model):
    _name = "hotel.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = "reservation_no desc"
    _inherit = ["mail.thread"]

    def _compute_folio_count(self):
        for res in self:
            res.update({"no_of_folio": len(res.folio_id.ids)})

    reservation_no = fields.Char(readonly=True, copy=False)
    date_order = fields.Datetime(
        "Date Ordered",
        readonly=True,
        required=True,
        index=True,
        default=lambda self: fields.Datetime.now(),
    )

    company_id = fields.Many2one(
        "res.company",
        "Hotel",
        readonly=True,
        index=True,
        required=True,
        default=lambda self: self.env.company,
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Guest Name",
        readonly=True,
        index=True,
        required=True,
    )
    pricelist_id = fields.Many2one(
        "product.pricelist",
        "Scheme",
        required=True,
        readonly=True,
        help="Pricelist for current reservation.",
    )
    partner_invoice_id = fields.Many2one(
        "res.partner",
        "Invoice Address",
        help="Invoice address for current reservation.",
    )
    partner_order_id = fields.Many2one(
        "res.partner",
        "Ordering Contact",
        readonly=True,
        help="The name and address of the "
        "contact that requested the order "
        "or quotation.",
    )
    partner_shipping_id = fields.Many2one(
        "res.partner",
        "Delivery Address",
        readonly=True,
        help="Delivery addressfor current reservation. ",
    )
    checkin = fields.Datetime(
        "Expected-Date-Arrival",
        required=True,
        readonly=True,
    )
    checkout = fields.Datetime(
        "Expected-Date-Departure",
        required=True,
        readonly=True,
    )
    adults = fields.Integer(
        readonly=True,
        required=True,
        help="List of adults there in guest list. ",
    )
    children = fields.Integer(
        readonly=True,
        help="Number of children there in guest list.",
    )
    reservation_line = fields.One2many(
        "hotel.reservation.line",
        "line_id",
        help="Hotel room reservation details.",
        readonly=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("cancel", "Cancel"),
            ("done", "Done"),
        ],
        readonly=True,
        default="draft",
    )
    folio_id = fields.Many2many(
        "hotel.folio",
        "hotel_folio_reservation_rel",
        "order_id",
        "invoice_id",
        string="Folio",
    )
    no_of_folio = fields.Integer("No. Folio", compute="_compute_folio_count")

    @api.ondelete(at_uninstall=False)
    def _unlink_except_non_draft(self):
        if any(reserv.state != "draft" for reserv in self):
            raise ValidationError(
                self.env._("You can only delete reservations in draft state!")
            )

    def copy(self):
        return super(HotelReservation, self.with_context(duplicate=True)).copy()

    @api.constrains("reservation_line", "adults", "children")
    def _check_reservation_rooms(self):
        """
        This method is used to validate the reservation_line.
        -----------------------------------------------------
        @param self: object pointer
        @return: raise a warning depending on the validation
        """
        for reservation in self:
            room_cap = []
            for rec in reservation.reservation_line:
                cap = 0
                if len(rec.reserve) == 0:
                    raise ValidationError(
                        self.env._("Please Select Rooms For Reservation.")
                    )
                cap = sum(room.capacity for room in rec.reserve)
                room_cap.append(cap)
            if not self.env.context.get("duplicate"):
                if (reservation.adults + reservation.children) > sum(room_cap):
                    raise ValidationError(
                        self.env._(
                            "Room Capacity Exceeded \n"
                            " Please Select Rooms According to"
                            " Members Accommodation."
                        )
                    )
            if reservation.adults <= 0:
                raise ValidationError(self.env._("Adults must be more than 0"))

    @api.constrains("checkin", "checkout")
    def check_in_out_dates(self):
        """
        When date_order is less than check-in date or
        Checkout date should be greater than the check-in date.
        """
        if self.checkout and self.checkin:
            # Compare days, not exact timestamps: date_order is stamped at
            # creation time, so a same-day check-in is valid (walk-in guest).
            if self.checkin.date() < self.date_order.date():
                raise ValidationError(
                    self.env._("Check-in date should be greater than the current date.")
                )
            if self.checkout < self.checkin:
                raise ValidationError(
                    self.env._("Check-out date should be greater than Check-in date.")
                )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("reservation_no"):
                vals["reservation_no"] = (
                    self.env["ir.sequence"].next_by_code("hotel.reservation") or "New"
                )
        return super().create(vals_list)

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
        vals_list = []

        # Collect all rooms to check for overlaps
        all_rooms = self.mapped("reservation_line.reserve")

        # Pre-fetch existing confirmed/done reservations for these rooms
        existing_reservations = reservation_line_obj.search(
            [
                ("status", "in", ("confirm", "done")),
                ("room_id", "in", all_rooms.ids),
            ]
        )

        # Group existing reservations by room_id
        existing_by_room = {}
        for res in existing_reservations:
            existing_by_room.setdefault(res.room_id.id, []).append(res)

        for reservation in self:
            reserv_checkin = reservation.checkin
            reserv_checkout = reservation.checkout

            for line in reservation.reservation_line:
                for room in line.reserve:
                    room_bool = False
                    room_reservations = existing_by_room.get(room.id, [])

                    for reserv in room_reservations:
                        check_in = reserv.check_in
                        check_out = reserv.check_out

                        # Overlap check logic
                        if (
                            (check_in <= reserv_checkin < check_out)
                            or (check_in < reserv_checkout <= check_out)
                            or (
                                reserv_checkin <= check_in
                                and reserv_checkout >= check_out
                            )
                        ):
                            room_bool = True
                            overlap_dates = self.check_overlap(
                                reservation.checkin.date(), reservation.checkout.date()
                            ) & self.check_overlap(
                                reserv.check_in.date(), reserv.check_out.date()
                            )
                            raise ValidationError(
                                self.env._(
                                    """You tried to Confirm Reservation with
                                    room %(room_name)s which is already
                                    reserved in this period.
                                    Overlap Dates: %(overlap_dates)s""",
                                    room_name=room.name,
                                    overlap_dates=overlap_dates,
                                )
                            )

                    if not room_bool:
                        vals_list.append(
                            {
                                "room_id": room.id,
                                "check_in": reservation.checkin,
                                "check_out": reservation.checkout,
                                "state": "assigned",
                                "reservation_id": reservation.id,
                            }
                        )
                        room.write({"isroom": False, "status": "occupied"})

            reservation.state = "confirm"

        if vals_list:
            reservation_line_obj.create(vals_list)
        return True

    def cancel_reservation(self):
        """
        This method cancel record set for hotel room reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: cancel record set for hotel room reservation line.
        """
        room_res_line_obj = self.env["hotel.room.reservation.line"]
        self.state = "cancel"

        # Batch delete room reservation lines
        room_reservation_lines = room_res_line_obj.search(
            [("reservation_id", "in", self.ids)]
        )
        room_reservation_lines.unlink()

        # Batch update rooms to available
        rooms = self.mapped("reservation_line.reserve")
        if rooms:
            rooms.write({"isroom": True, "status": "available"})
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
            "default_res_ids": self.ids,
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
                "company_id": reservation.company_id.id,
                "partner_id": reservation.partner_id.id,
                "pricelist_id": reservation.pricelist_id.id,
                "partner_invoice_id": reservation.partner_invoice_id.id
                or reservation.partner_id.id,
                "partner_shipping_id": reservation.partner_shipping_id.id
                or reservation.partner_id.id,
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
                    rm_line._onchange_product_id_warning()
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
        configured_addition_hours = self.company_id.additional_hours
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
    _name = "hotel.reservation.line"
    _description = "Reservation Line"

    name = fields.Char()
    line_id = fields.Many2one("hotel.reservation")
    reserve = fields.Many2many(
        "hotel.room",
        "hotel_reservation_line_room_rel",
        "hotel_reservation_line_id",
        "room_id",
        domain="[('isroom','=',True),\
                               ('room_categ_id','=',categ_id)]",
    )
    categ_id = fields.Many2one("hotel.room.type", "Room Type")

    @api.onchange("categ_id")
    def on_change_categ(self):
        """
        When you change categ_id it check checkin and checkout are
        filled or not if not then raise warning
        ---------------
        @param self: object pointer
        """
        checkin = self.line_id.checkin
        checkout = self.line_id.checkout
        if not checkin or not checkout:
            raise ValidationError(
                self.env._(
                    "Before choosing a room,\n You have to "
                    "select a Check in date and a Check out "
                    " date in the reservation form."
                )
            )

        # Search for all rooms of the selected category
        rooms = self.env["hotel.room"].search(
            [("room_categ_id", "=", self.categ_id.id)]
        )

        # Batch search for all overlapping reservation lines
        overlapping_res = self.env["hotel.room.reservation.line"].search(
            [
                ("room_id", "in", rooms.ids),
                ("status", "!=", "cancel"),
                "|",
                "|",
                "&",
                ("check_in", "<=", checkin),
                ("check_out", ">", checkin),
                "&",
                ("check_in", "<", checkout),
                ("check_out", ">=", checkout),
                "&",
                ("check_in", ">=", checkin),
                ("check_out", "<=", checkout),
            ]
        )
        reserved_room_ids = overlapping_res.mapped("room_id").ids

        # Batch search for all overlapping folio room lines
        overlapping_folio = self.env["folio.room.line"].search(
            [
                ("room_id", "in", rooms.ids),
                ("status", "!=", "cancel"),
                "|",
                "|",
                "&",
                ("check_in", "<=", checkin),
                ("check_out", ">", checkin),
                "&",
                ("check_in", "<", checkout),
                ("check_out", ">=", checkout),
                "&",
                ("check_in", ">=", checkin),
                ("check_out", "<=", checkout),
            ]
        )
        reserved_room_ids += overlapping_folio.mapped("room_id").ids

        available_room_idsList = [r.id for r in rooms if r.id not in reserved_room_ids]
        return {"domain": {"reserve": [("id", "in", available_room_idsList)]}}

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
        return super().unlink()


class HotelRoomReservationLine(models.Model):
    _name = "hotel.room.reservation.line"
    _description = "Hotel Room Reservation"
    _rec_name = "room_id"

    room_id = fields.Many2one("hotel.room")
    check_in = fields.Datetime("Check In Date", required=True)
    check_out = fields.Datetime("Check Out Date", required=True)
    state = fields.Selection(
        [("assigned", "Assigned"), ("unassigned", "Unassigned")], "Room Status"
    )
    reservation_id = fields.Many2one("hotel.reservation", "Reservation")
    status = fields.Selection(string="state", related="reservation_id.state")
