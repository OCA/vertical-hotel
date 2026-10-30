# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command

# Table bookings in these states hold their tables.
TABLE_HOLDING_STATES = ("confirm", "order")


def _check_state(records, allowed, action):
    """Refuse ``action`` on the records whose state is not in ``allowed``
    (the buttons hide it, server actions and RPC do not)."""
    wrong = records.filtered(lambda r: r.state not in allowed)
    if wrong:
        raise UserError(
            records.env._(
                "%(action)s is not possible for %(records)s.",
                action=action,
                records=", ".join(wrong.mapped("display_name")),
            )
        )


def _room_product_domain(model):
    """Domain of the products that are hotel rooms."""
    return [("id", "in", model.env["hotel.room"].sudo().search([]).product_id.ids)]


def _create_kot(env, header, order_lines):
    """Create a kitchen order ticket with a copy of ``order_lines``."""
    return env["hotel.restaurant.kitchen.order.tickets"].create(
        dict(
            header,
            kot_list_ids=[
                Command.create(
                    {
                        "menucard_id": line.menucard_id.id,
                        "item_qty": line.item_qty,
                        "item_rate": line.item_rate,
                    }
                )
                for line in order_lines
            ],
        )
    )


def _charge_folio(folio, order_lines):
    """Add ``order_lines`` to the folio as service lines."""
    sale_lines = folio.env["sale.order.line"].create(
        [
            {
                "order_id": folio.order_id.id,
                "name": line.menucard_id.name,
                "product_id": line.menucard_id.product_id.id,
                "product_uom_id": line.menucard_id.uom_id.id,
                "product_uom_qty": line.item_qty,
                "price_unit": line.item_rate,
            }
            for line in order_lines
        ]
    )
    folio.env["hotel.service.line"].create(
        [
            {"folio_id": folio.id, "service_line_id": sale_line.id}
            for sale_line in sale_lines
        ]
    )


class HotelRestaurantTables(models.Model):
    _name = "hotel.restaurant.tables"
    _description = "Includes Hotel Restaurant Table"

    name = fields.Char("Table Number", required=True)
    capacity = fields.Integer()


class HotelRestaurantReservation(models.Model):
    _name = "hotel.restaurant.reservation"
    _description = "Includes Hotel Restaurant Reservation"
    _rec_name = "reservation_id"

    def create_order(self):
        """
        This method is for create a new order for hotel restaurant
        reservation .when table is booked and create order button is
        clicked then this method is called and order is created. You
        can see this created order in "Orders"
        ------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel restaurant reservation.
        """
        _check_state(self, ("confirm", "done"), self.env._("Creating an order"))
        self.env["hotel.reservation.order"].create(
            [
                {
                    "reservation_id": record.id,
                    "order_date": record.start_date,
                    "room_id": record.room_id.id,
                    "folio_id": record.folio_id.id,
                    "table_nos_ids": [Command.set(record.table_nos_ids.ids)],
                    "is_folio": record.is_folio,
                }
                for record in self
            ]
        )
        self.write({"state": "order"})
        return True

    @api.onchange("customer_id")
    def _onchange_partner_id(self):
        """
        When Customer name is changed respective address will display
        in address field
        @param self: object pointer
        """
        if not self.customer_id:
            self.partner_address_id = False
        else:
            addr = self.customer_id.address_get(["default"])
            self.partner_address_id = addr["default"]

    @api.onchange("folio_id")
    def _onchange_folio_id(self):
        folio = self.folio_id
        self.customer_id = folio.partner_id
        self.room_id = folio.room_line_ids[:1].product_id

    def action_set_to_draft(self):
        """
        This method is used to change the state
        to draft of the hotel restaurant reservation
        --------------------------------------------
        @param self: object pointer
        """
        _check_state(self, ("cancel",), self.env._("Resetting to draft"))
        self.write({"state": "draft"})

    def table_reserved(self):
        """
        when CONFIRM BUTTON is clicked this method is called for
        table reservation
        @param self: The object pointer
        @return: change a state depending on the condition
        """
        _check_state(self, ("draft",), self.env._("Confirming"))
        for reservation in self:
            if not reservation.table_nos_ids:
                raise ValidationError(
                    self.env._("Please Select Tables For Reservation")
                )
            # a booking ending when the next one starts does not block it
            taken = self.search(
                [
                    ("id", "!=", reservation.id),
                    ("state", "in", TABLE_HOLDING_STATES),
                    ("table_nos_ids", "in", reservation.table_nos_ids.ids),
                    ("start_date", "<", reservation.end_date),
                    ("end_date", ">", reservation.start_date),
                ],
                limit=1,
            )
            if taken:
                raise ValidationError(
                    self.env._(
                        "You tried to confirm reservation "
                        "with tables that are already reserved "
                        "in this reservation period"
                    )
                )
            reservation.state = "confirm"
        return True

    def table_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel restaurant reservation
        --------------------------------------------
        @param self: object pointer
        """
        _check_state(self, ("draft", "confirm"), self.env._("Cancelling"))
        self.write({"state": "cancel"})

    def table_done(self):
        """
        This method is used to change the state
        to done of the hotel restaurant reservation
        --------------------------------------------
        @param self: object pointer
        """
        _check_state(self, ("confirm", "order"), self.env._("Setting to done"))
        self.write({"state": "done"})

    reservation_id = fields.Char("Reservation No", readonly=True, index=True)
    room_id = fields.Many2one(
        "product.product", "Room No", domain=lambda self: _room_product_domain(self)
    )
    folio_id = fields.Many2one("hotel.folio", "Folio No")
    start_date = fields.Datetime(
        "Start Time", required=True, default=lambda self: fields.Datetime.now()
    )
    end_date = fields.Datetime("End Time", required=True)
    customer_id = fields.Many2one("res.partner", "Customer Name", required=True)
    partner_address_id = fields.Many2one("res.partner", "Address")
    table_nos_ids = fields.Many2many(
        "hotel.restaurant.tables",
        "reservation_table",
        "reservation_table_id",
        "name",
        string="Table Number",
        help="Table reservation detail.",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
            ("order", "Order Created"),
        ],
        "state",
        required=True,
        readonly=True,
        copy=False,
        default="draft",
    )
    is_folio = fields.Boolean("Is a Hotel Guest??")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        seq_obj = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("reservation_id"):
                vals["reservation_id"] = (
                    seq_obj.next_by_code("hotel.restaurant.reservation") or "New"
                )
        return super().create(vals_list)

    @api.constrains("start_date", "end_date", "folio_id", "is_folio")
    def _check_start_dates(self):
        """
        This method is used to validate the start_date and end_date.
        -------------------------------------------------------------
        @param self: object pointer
        @return: raise a warning depending on the validation
        """
        for reservation in self:
            if reservation.start_date >= reservation.end_date:
                raise ValidationError(
                    self.env._("Start Date Should be less than the End Date!")
                )
            if not reservation.is_folio:
                continue
            for line in reservation.folio_id.room_line_ids:
                if reservation.start_date < line.checkin_date:
                    raise ValidationError(
                        self.env._(
                            "Start Date Should be greater than the Folio Check-in Date!"
                        )
                    )
                if reservation.end_date > line.checkout_date:
                    raise ValidationError(
                        self.env._(
                            "End Date Should be less than the Folio Check-out Date!"
                        )
                    )


class HotelRestaurantKitchenOrderTickets(models.Model):
    _name = "hotel.restaurant.kitchen.order.tickets"
    _description = "Includes Hotel Restaurant Order"
    _rec_name = "order_number"

    order_number = fields.Char(readonly=True)
    reservation_number = fields.Char()
    kot_date = fields.Datetime("Date")
    room_no = fields.Char(readonly=True)
    waiter_name = fields.Char(readonly=True)
    table_nos_ids = fields.Many2many(
        "hotel.restaurant.tables",
        "restaurant_kitchen_order_rel",
        "table_no",
        "name",
        "Table Number",
        help="Table reservation detail.",
    )
    kot_list_ids = fields.One2many(
        "hotel.restaurant.order.list",
        "kot_order_id",
        "Order List",
        help="Kitchen order list",
    )


class HotelRestaurantOrder(models.Model):
    _name = "hotel.restaurant.order"
    _description = "Includes Hotel Restaurant Order"
    _rec_name = "order_no"

    @api.depends("order_list_ids.price_subtotal", "tax")
    def _compute_amount_all_total(self):
        """
        amount_subtotal and amount_total will display on change of order_list_ids
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        for sale in self:
            sale.amount_subtotal = sum(sale.order_list_ids.mapped("price_subtotal"))
            sale.amount_total = sale.amount_subtotal * (1 + sale.tax / 100)

    def done_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel restaurant order
        ----------------------------------------
        @param self: object pointer
        """
        # a done order is on the folio: remove the charge there first
        _check_state(self, ("draft", "order"), self.env._("Cancelling"))
        self.write({"state": "cancel"})

    def set_to_draft(self):
        """
        This method is used to change the state
        to draft of the hotel restaurant order
        ----------------------------------------
        @param self: object pointer
        """
        _check_state(self, ("cancel",), self.env._("Resetting to draft"))
        self.write({"state": "draft"})

    def _kot_header(self):
        self.ensure_one()
        return {
            "order_number": self.order_no,
            "kot_date": fields.Datetime.now(),
            "room_no": self.room_id.name,
            "waiter_name": self.waiter_id.name,
            "table_nos_ids": [Command.set(self.table_nos_ids.ids)],
        }

    def generate_kot(self):
        """
        This method create new record for hotel restaurant order list.
        @param self: The object pointer
        @return: new record set for hotel restaurant order list.
        """
        _check_state(self, ("draft",), self.env._("Sending to the kitchen"))
        for order in self:
            if not order.order_list_ids:
                raise ValidationError(self.env._("Please specify items for the order"))
            if not order.table_nos_ids:
                raise ValidationError(self.env._("Please Assign a Table"))
            kot = _create_kot(
                self.env,
                dict(order._kot_header(), kot_date=order.o_date),
                order.order_list_ids,
            )
            order.write(
                {
                    "kitchen": kot.id,
                    "rest_item_id": [Command.set(order.order_list_ids.ids)],
                    "state": "order",
                }
            )
        return True

    def generate_kot_update(self):
        """
        Send the lines added since the last ticket to the kitchen, on one
        new kitchen order ticket.
        ----------------------------------------------------------
        @param self: The object pointer
        @return: True
        """
        _check_state(self, ("order",), self.env._("Updating the kitchen order"))
        for order in self:
            new_lines = order.order_list_ids - order.rest_item_id
            if not new_lines:
                continue
            kot = _create_kot(self.env, order._kot_header(), new_lines)
            order.write(
                {
                    "kitchen": kot.id,
                    "rest_item_id": [Command.link(line.id) for line in new_lines],
                }
            )
        return True

    def done_order_kot(self):
        """
        This method is used to change the state
        to done of the hotel restaurant order
        ----------------------------------------
        @param self: object pointer
        """
        # only once: a done order is already on the folio
        _check_state(self, ("order",), self.env._("Closing the order"))
        for order in self.filtered("folio_id"):
            if order.order_list_ids:
                _charge_folio(order.folio_id, order.order_list_ids)
                order.folio_id.write(
                    {"hotel_restaurant_orders_ids": [Command.link(order.id)]}
                )
        self.write({"state": "done"})
        return True

    order_no = fields.Char("Order Number", readonly=True)
    o_date = fields.Datetime(
        "Order Date", required=True, default=lambda self: fields.Datetime.now()
    )
    room_id = fields.Many2one(
        "product.product", "Room No", domain=lambda self: _room_product_domain(self)
    )
    folio_id = fields.Many2one("hotel.folio", "Folio No")
    waiter_id = fields.Many2one("res.partner")
    table_nos_ids = fields.Many2many(
        "hotel.restaurant.tables",
        "restaurant_table_order_rel",
        "table_no",
        "name",
        "Table Number",
    )
    order_list_ids = fields.One2many(
        "hotel.restaurant.order.list", "restaurant_order_id"
    )
    tax = fields.Float("Tax (%) ")
    amount_subtotal = fields.Float(
        compute="_compute_amount_all_total", string="Subtotal"
    )
    amount_total = fields.Float(compute="_compute_amount_all_total", string="Total")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("order", "Order Created"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        required=True,
        readonly=True,
        copy=False,
        default="draft",
    )
    is_folio = fields.Boolean(
        "Is a Hotel Guest??", help="is customer residing in hotel or not"
    )
    customer_id = fields.Many2one("res.partner", "Customer Name", required=True)
    kitchen = fields.Integer(help="Last kitchen order ticket of the order.")
    rest_item_id = fields.Many2many(
        "hotel.restaurant.order.list",
        "restaurant_kitchen_rel",
        "restau_id",
        "kit_id",
        "Rest",
        help="Order lines already sent to the kitchen.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        seq_obj = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("order_no"):
                vals["order_no"] = (
                    seq_obj.next_by_code("hotel.restaurant.order") or "New"
                )
        return super().create(vals_list)

    @api.onchange("folio_id")
    def _onchange_folio_id(self):
        if self.folio_id:
            room_line = self.folio_id.room_line_ids[:1]
            if room_line:
                self.update(
                    {
                        "customer_id": self.folio_id.partner_id.id,
                        "room_id": room_line.product_id.id,
                    }
                )


class HotelReservationOrder(models.Model):
    _name = "hotel.reservation.order"
    _description = "Reservation Order"
    _rec_name = "order_number"

    room_id = fields.Many2one(
        "product.product", "Room No", domain=lambda self: _room_product_domain(self)
    )

    @api.depends("order_list_ids.price_subtotal", "tax")
    def _compute_amount_all_total(self):
        """
        amount_subtotal and amount_total will display on change of order_list_ids
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        for sale in self:
            sale.amount_subtotal = sum(sale.order_list_ids.mapped("price_subtotal"))
            sale.amount_total = sale.amount_subtotal * (1 + sale.tax / 100)

    @api.onchange("reservation_id")
    def _onchange_reservation_id(self):
        if self.reservation_id:
            self.table_nos_ids = self.reservation_id.table_nos_ids
            self.folio_id = self.reservation_id.folio_id
            self.room_id = self.reservation_id.room_id.id

    @api.onchange("folio_id")
    def _onchange_folio_id(self):
        if self.folio_id:
            self.room_id = self.folio_id.room_line_ids[:1].product_id.id

    def _kot_header(self):
        self.ensure_one()
        return {
            "order_number": self.order_number,
            "reservation_number": self.reservation_id.reservation_id,
            "kot_date": fields.Datetime.now(),
            "room_no": self.room_id.name,
            "waiter_name": self.waiter_id.name,
            "table_nos_ids": [Command.set(self.table_nos_ids.ids)],
        }

    def reservation_generate_kot(self):
        """
        This method creates the kitchen order ticket of the order.
        --------------------------------------------------------------
        @param self: The object pointer
        @return: True
        """
        _check_state(self, ("draft",), self.env._("Sending to the kitchen"))
        for order in self:
            if not order.order_list_ids:
                raise ValidationError(self.env._("Please specify items for the order"))
            kot = _create_kot(
                self.env,
                dict(order._kot_header(), kot_date=order.order_date),
                order.order_list_ids,
            )
            order.write(
                {
                    "kitchen": kot.id,
                    "rests_ids": [Command.set(order.order_list_ids.ids)],
                    "state": "order",
                }
            )
        return True

    def reservation_update_kot(self):
        """
        Send the lines added since the last ticket to the kitchen, on one
        new kitchen order ticket.
        ----------------------------------------------------------
        @param self: The object pointer
        @return: True
        """
        _check_state(self, ("order",), self.env._("Updating the kitchen order"))
        for order in self:
            new_lines = order.order_list_ids - order.rests_ids
            if not new_lines:
                continue
            kot = _create_kot(self.env, order._kot_header(), new_lines)
            order.write(
                {
                    "kitchen": kot.id,
                    "rests_ids": [Command.link(line.id) for line in new_lines],
                }
            )
        return True

    def done_kot(self):
        """
        This method is used to change the state
        to done of the hotel reservation order
        ----------------------------------------
        @param self: object pointer
        """
        # only once: a done order is already on the folio
        _check_state(self, ("order",), self.env._("Closing the order"))
        for order in self:
            if order.folio_id and order.order_list_ids:
                _charge_folio(order.folio_id, order.order_list_ids)
                order.folio_id.write(
                    {"hotel_reservation_orders_ids": [Command.link(order.id)]}
                )
        self.reservation_id.filtered(lambda r: r.state != "cancel").write(
            {"state": "done"}
        )
        self.write({"state": "done"})
        return True

    order_number = fields.Char("Order No", readonly=True)
    reservation_id = fields.Many2one("hotel.restaurant.reservation", "Reservation No")
    order_date = fields.Datetime(
        "Date", required=True, default=lambda self: fields.Datetime.now()
    )
    waiter_id = fields.Many2one("res.partner", "Waiter Name")
    table_nos_ids = fields.Many2many(
        "hotel.restaurant.tables",
        "temp_table4",
        "table_no",
        "name",
        "Table Number",
    )
    order_list_ids = fields.One2many(
        "hotel.restaurant.order.list", "reservation_order_id"
    )
    tax = fields.Float("Tax (%) ")
    amount_subtotal = fields.Float(
        compute="_compute_amount_all_total", string="Subtotal"
    )
    amount_total = fields.Float(compute="_compute_amount_all_total", string="Total")
    kitchen = fields.Integer("Kitchen Id", help="Last kitchen order ticket.")
    rests_ids = fields.Many2many(
        "hotel.restaurant.order.list",
        "reserv_id",
        "kitchen_id",
        "res_kit_ids",
        "Rest",
        help="Order lines already sent to the kitchen.",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("order", "Order Created"), ("done", "Done")],
        required=True,
        readonly=True,
        default="draft",
    )
    folio_id = fields.Many2one("hotel.folio", "Folio No")
    is_folio = fields.Boolean(
        "Is a Hotel Guest??", help="is customer residing in hotel or not"
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        seq_obj = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("order_number"):
                vals["order_number"] = (
                    seq_obj.next_by_code("hotel.reservation.order") or "New"
                )
        return super().create(vals_list)


class HotelRestaurantOrderList(models.Model):
    _name = "hotel.restaurant.order.list"
    _description = "Includes Hotel Restaurant Order"

    @api.depends("item_qty", "item_rate")
    def _compute_price_subtotal(self):
        """
        price_subtotal will display on change of item_rate
        --------------------------------------------------
        @param self: object pointer
        """
        for line in self:
            line.price_subtotal = line.item_rate * line.item_qty

    @api.onchange("menucard_id")
    def _onchange_item_name(self):
        """
        item rate will display on change of item name
        ---------------------------------------------
        @param self: object pointer
        """
        self.item_rate = self.menucard_id.list_price

    restaurant_order_id = fields.Many2one(
        "hotel.restaurant.order", index=True, ondelete="cascade"
    )
    reservation_order_id = fields.Many2one(
        "hotel.reservation.order", index=True, ondelete="cascade"
    )
    kot_order_id = fields.Many2one(
        "hotel.restaurant.kitchen.order.tickets",
        "Kitchen Order Tickets",
        index=True,
        ondelete="cascade",
    )
    menucard_id = fields.Many2one("hotel.menucard", "Item Name", required=True)
    item_qty = fields.Integer("Qty", required=True, default=1)
    item_rate = fields.Float("Rate")
    price_subtotal = fields.Float(compute="_compute_price_subtotal", string="Subtotal")
