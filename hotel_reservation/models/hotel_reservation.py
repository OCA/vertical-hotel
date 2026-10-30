# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, time, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command


class HotelReservation(models.Model):
    _name = "hotel.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = "reservation_no desc"
    _inherit = "mail.thread"

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
        help="Delivery address for current reservation.",
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
    guest_ids = fields.One2many(
        "hotel.guest",
        "reservation_id",
        string="Accompanying Guests",
        help="Everyone staying besides the main guest. Each one is filed "
        "as a child contact of the main guest.",
    )
    adults = fields.Integer(
        compute="_compute_guest_counts",
        store=True,
        readonly=True,
        help="Main guest plus every accompanying guest marked as an adult.",
    )
    children = fields.Integer(
        compute="_compute_guest_counts",
        store=True,
        readonly=True,
        help="Accompanying guests marked as children.",
    )
    total_guest = fields.Integer(
        compute="_compute_guest_counts",
        store=True,
        string="Total Guests",
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
        tracking=True,
    )
    folio_id = fields.Many2many(
        "hotel.folio",
        "hotel_folio_reservation_rel",
        "order_id",
        "invoice_id",
    )
    no_of_folio = fields.Integer("No. Folio", compute="_compute_folio_count")

    @api.depends("folio_id")
    def _compute_folio_count(self):
        for res in self:
            res.no_of_folio = len(res.folio_id)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_non_draft(self):
        if any(reserv.state != "draft" for reserv in self):
            raise ValidationError(
                self.env._("You can only delete reservations in draft state!")
            )

    @api.depends("guest_ids", "guest_ids.guest_type")
    def _compute_guest_counts(self):
        for rec in self:
            # The main guest occupies a bed too, and always counts as an
            # adult - guest_ids holds only the people accompanying them.
            adults = 1 + len(rec.guest_ids.filtered(lambda g: g.guest_type == "adult"))
            children = len(rec.guest_ids.filtered(lambda g: g.guest_type == "child"))
            rec.adults = adults
            rec.children = children
            rec.total_guest = adults + children

    def write(self, vals):
        res = super().write(vals)
        if vals.get("partner_id"):
            # Guests are filed under whoever is booking; if that changes,
            # the contacts have to move with it or they stay attached to
            # the previous guest.
            for rec in self:
                rec.guest_ids.partner_id.write({"parent_id": rec.partner_id.id})
        return res

    def copy(self, default=None):
        return super(HotelReservation, self.with_context(duplicate=True)).copy(
            default=default
        )

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
                if len(rec.reserve) == 0:
                    raise ValidationError(
                        self.env._("Please Select Rooms For Reservation.")
                    )
                room_cap.append(sum(room.capacity for room in rec.reserve))
            if not self.env.context.get("duplicate") and (
                reservation.adults + reservation.children
            ) > sum(room_cap):
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
        for reservation in self:
            if not (reservation.checkout and reservation.checkin):
                continue
            # Compare days, not exact timestamps: date_order is stamped at
            # creation time, so a same-day check-in is valid (walk-in guest).
            if reservation.checkin.date() < reservation.date_order.date():
                raise ValidationError(
                    self.env._("Check-in date should be greater than the current date.")
                )
            if reservation.checkout < reservation.checkin:
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

    def _check_state(self, allowed, action):
        wrong = self.filtered(lambda r: r.state not in allowed)
        if wrong:
            raise UserError(
                self.env._(
                    "%(action)s is not possible for %(reservations)s.",
                    action=action,
                    reservations=", ".join(wrong.mapped("reservation_no")),
                )
            )

    def confirmed_reservation(self):
        """
        This method create a new record set for hotel room reservation line
        -------------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel room reservation line.
        """
        self._check_state(("draft",), self.env._("Confirming"))
        room_obj = self.env["hotel.room"]
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        # one reservation at a time: the rooms booked by the previous ones
        # in self are already taken
        for reservation in self:
            rooms = reservation.reservation_line.reserve
            busy = rooms & room_obj._get_booked_rooms(
                reservation.checkin, reservation.checkout
            )
            if busy:
                raise ValidationError(
                    self.env._(
                        "You tried to Confirm Reservation with room %(room_name)s "
                        "which is already reserved in this period.",
                        room_name=", ".join(busy.mapped("name")),
                    )
                )
            reservation_line_obj.create(
                [
                    {
                        "room_id": room.id,
                        "check_in": reservation.checkin,
                        "check_out": reservation.checkout,
                        "state": "assigned",
                        "reservation_id": reservation.id,
                    }
                    for room in rooms
                ]
            )
            reservation.state = "confirm"
        self.reservation_line.reserve._update_room_status()
        return True

    def cancel_reservation(self):
        """
        This method cancel record set for hotel room reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: cancel record set for hotel room reservation line.
        """
        self._check_state(("draft", "confirm"), self.env._("Cancelling"))
        self.state = "cancel"
        self.env["hotel.room.reservation.line"].search(
            [("reservation_id", "in", self.ids)]
        ).unlink()
        self.reservation_line.reserve._update_room_status()
        return True

    def set_to_draft_reservation(self):
        self._check_state(("cancel",), self.env._("Resetting to draft"))
        self.state = "draft"

    def action_send_reservation_mail(self):
        """
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        """
        self.ensure_one()
        template = self.env.ref("hotel_reservation.email_template_hotel_reservation")
        compose_form = self.env.ref("mail.email_compose_message_wizard_form")
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "target": "new",
            "context": {
                "default_model": "hotel.reservation",
                "default_res_ids": self.ids,
                "default_template_id": template.id,
                "default_composition_mode": "comment",
            },
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
        template = self.env.ref(
            "hotel_reservation.mail_template_reservation_reminder_24hrs"
        )
        tomorrow = datetime.combine(
            fields.Date.context_today(self) + timedelta(days=1), time.min
        )
        reservations = self.search(
            [
                ("state", "=", "confirm"),
                ("checkin", ">=", tomorrow),
                ("checkin", "<", tomorrow + timedelta(days=1)),
                ("partner_id.email", "!=", False),
            ]
        )
        for reservation in reservations:
            template.send_mail(reservation.id)
        return True

    def create_folio(self):
        """
        This method is for create new hotel folio.
        -----------------------------------------
        @param self: The object pointer
        @return: new record set for hotel folio.
        """
        self._check_state(("confirm",), self.env._("Creating a folio"))
        hotel_folio_obj = self.env["hotel.folio"]
        for reservation in self:
            duration = (
                reservation._onchange_check_dates(
                    checkin_date=reservation.checkin,
                    checkout_date=reservation.checkout,
                ).get("duration")
                or 0.0
            )
            folio = hotel_folio_obj.create(
                {
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
                    # Link the folio to the contacts the reservation already
                    # created. Copying name/email/phone into new guest lines
                    # would create each guest's contact a second time, since
                    # every hotel.guest delegates to its own res.partner.
                    "guest_ids": [
                        Command.create(
                            {
                                "partner_id": guest.partner_id.id,
                                "guest_type": guest.guest_type,
                            }
                        )
                        for guest in reservation.guest_ids
                    ],
                    "room_line_ids": [
                        Command.create(
                            {
                                "checkin_date": reservation.checkin,
                                "checkout_date": reservation.checkout,
                                "product_id": room.product_id.id,
                                "name": reservation.reservation_no,
                                "price_unit": room.list_price,
                                "product_uom_qty": duration,
                                "is_reserved": True,
                            }
                        )
                        for room in reservation.reservation_line.reserve
                    ],
                }
            )
            for rm_line in folio.room_line_ids:
                rm_line._onchange_product_id_warning()
            reservation.write({"folio_id": [Command.set(folio.ids)], "state": "done"})
        self.reservation_line.reserve._update_room_status()
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
        # Same rule as hotel.folio.line._onchange_checkin_checkout_dates, so
        # the folio created from the reservation keeps the same quantity when
        # its dates are edited: whole days, a started day counts as a day.
        configured_addition_hours = self.company_id.additional_hours
        duration = 0
        if checkin_date and checkout_date:
            dur = checkout_date - checkin_date
            duration = dur.days + 1 if dur.seconds else dur.days
            if (
                configured_addition_hours > 0
                and dur.seconds / 3600 >= configured_addition_hours
            ):
                duration += 1
        return {"duration": duration}

    def open_folio_view(self):
        folios = self.mapped("folio_id")
        action_xmlid = "vertical_hotel.open_hotel_folio1_form_tree_all"
        action = self.env["ir.actions.act_window"]._for_xml_id(action_xmlid)
        if len(folios) > 1:
            action["domain"] = [("id", "in", folios.ids)]
        elif len(folios) == 1:
            form_view = self.env.ref("vertical_hotel.view_hotel_folio_form")
            action["views"] = [(form_view.id, "form")]
            action["res_id"] = folios.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action


class HotelReservationLine(models.Model):
    _name = "hotel.reservation.line"
    _description = "Reservation Line"

    name = fields.Char()
    line_id = fields.Many2one("hotel.reservation", index=True, ondelete="cascade")
    reserve = fields.Many2many(
        "hotel.room",
        "hotel_reservation_line_room_rel",
        "hotel_reservation_line_id",
        "room_id",
        domain="[('id', 'in', available_room_ids)]",
    )
    categ_id = fields.Many2one("hotel.room.type", "Room Type")
    available_room_ids = fields.Many2many(
        "hotel.room",
        compute="_compute_available_room_ids",
        help="Rooms of the room type that are free for the stay.",
    )

    @api.depends("categ_id", "line_id.checkin", "line_id.checkout")
    def _compute_available_room_ids(self):
        room_obj = self.env["hotel.room"]
        for line in self:
            domain = [("room_categ_id", "=", line.categ_id.id)] if line.categ_id else []
            rooms = room_obj.search(domain)
            reservation = line.line_id
            if reservation.checkin and reservation.checkout:
                rooms -= room_obj._get_booked_rooms(
                    reservation.checkin,
                    reservation.checkout,
                    exclude_reservations=reservation._origin,
                )
            line.available_room_ids = rooms

    @api.onchange("categ_id")
    def on_change_categ(self):
        """
        When you change categ_id it check checkin and checkout are
        filled or not if not then show a warning
        ---------------
        @param self: object pointer
        """
        if self.categ_id and not (self.line_id.checkin and self.line_id.checkout):
            return {
                "warning": {
                    "title": self.env._("Missing dates"),
                    "message": self.env._(
                        "Before choosing a room,\n You have to "
                        "select a Check in date and a Check out "
                        " date in the reservation form."
                    ),
                }
            }

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        bookings = self.env["hotel.room.reservation.line"]
        for line in self:
            bookings |= bookings.search(
                [
                    ("room_id", "in", line.reserve.ids),
                    ("reservation_id", "=", line.line_id.id),
                ]
            )
        rooms = bookings.room_id
        bookings.unlink()
        res = super().unlink()
        rooms._update_room_status()
        return res


class HotelRoomReservationLine(models.Model):
    _name = "hotel.room.reservation.line"
    _description = "Hotel Room Reservation"
    _rec_name = "room_id"

    room_id = fields.Many2one("hotel.room", index=True)
    check_in = fields.Datetime("Check In Date", required=True, index=True)
    check_out = fields.Datetime("Check Out Date", required=True, index=True)
    state = fields.Selection(
        [("assigned", "Assigned"), ("unassigned", "Unassigned")], "Room Status"
    )
    reservation_id = fields.Many2one("hotel.reservation", index=True)
    status = fields.Selection(string="state", related="reservation_id.state")
