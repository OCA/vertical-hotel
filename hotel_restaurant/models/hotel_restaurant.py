# See LICENSE file for full copyright and licensing details.

import time

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class HotelRestaurantTables(models.Model):

    _name = "hotel.restaurant.tables"
    _description = "Includes Hotel Restaurant Table"

    name = fields.Char("Table Number", required=True)
    capacity = fields.Integer("Capacity")


class HotelRestaurantReservation(models.Model):

    _name = "hotel.restaurant.reservation"
    _description = "Includes Hotel Restaurant Reservation"
    _rec_name = "reservation_id"

    def create_order(self):
        """
        This method is for create a new order for hotel restaurant
        reservation .when table is booked and create order button is
        clicked then this method is called and order is created.you
        can see this created order in "Orders"
        ------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel restaurant reservation.
        """
        reservation_order = self.env["hotel.reservation.order"]
        for record in self:
            table_ids = [tableno.id for tableno in record.table_nos_ids]
            values = {
                "reservationno": record.id,
                "order_date": record.start_date,
                "folio_id": record.folio_id.id,
                "table_nos_ids": [(6, 0, table_ids)],
                "is_folio": record.is_folio,
            }
            reservation_order.create(values)
        self.write({"state": "order"})
        return True

    @api.onchange("customer_id")
    def _onchange_partner_id(self):
        """
        When Customer name is changed respective adress will display
        in Adress field
        @param self: object pointer
        """
        if not self.customer_id:
            self.partner_address_id = False
        else:
            addr = self.customer_id.address_get(["default"])
            self.partner_address_id = addr["default"]

    @api.onchange("folio_id")
    def _onchange_folio_id(self):
        """
        When you change folio_id, based on that it will update
        the customer_id and room_number as well
        ---------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.write({"customer_id": False, "room_id": False})
            if rec.folio_id:
                rec.customer_id = rec.folio_id.partner_id.id
                if rec.folio_id.room_lines:
                    rec.room_id = rec.folio_id.room_lines[0].product_id.id

    def action_set_to_draft(self):
        """
        This method is used to change the state
        to draft of the hotel restaurant reservation
        --------------------------------------------
        @param self: object pointer
        """
        self.write({"state": "draft"})

    def table_reserved(self):
        """
        when CONFIRM BUTTON is clicked this method is called for
        table reservation
        @param self: The object pointer
        @return: change a state depending on the condition
        """
        for reservation in self:
            self._cr.execute(
                "select count(*) from "
                "hotel_restaurant_reservation as hrr "
                "inner join reservation_table as rt on \
                             rt.reservation_table_id = hrr.id "
                "where (start_date,end_date)overlaps\
                             ( timestamp %s , timestamp %s ) "
                "and hrr.id<> %s and state != 'done'"
                "and rt.name in (select rt.name from \
                             hotel_restaurant_reservation as hrr "
                "inner join reservation_table as rt on \
                             rt.reservation_table_id = hrr.id "
                "where hrr.id= %s) ",
                (
                    reservation.start_date,
                    reservation.end_date,
                    reservation.id,
                    reservation.id,
                ),
            )
            res = self._cr.fetchone()
            roomcount = res and res[0] or 0.0
            if len(reservation.table_nos_ids.ids) == 0:
                raise ValidationError(
                    _(
                        "Please Select Tables For \
                                         Reservation"
                    )
                )
            if roomcount:
                raise ValidationError(
                    _(
                        "You tried to confirm reservation \
                                         with table those already reserved \
                                         in this reservation period"
                    )
                )
            self.state = "confirm"
            return True

    def table_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel restaurant reservation
        --------------------------------------------
        @param self: object pointer
        """
        self.write({"state": "cancel"})

    def table_done(self):
        """
        This method is used to change the state
        to done of the hotel restaurant reservation
        --------------------------------------------
        @param self: object pointer
        """
        self.write({"state": "done"})

    reservation_id = fields.Char("Reservation No", readonly=True, index=True)
    room_id = fields.Many2one("product.product", "Room No")
    folio_id = fields.Many2one("hotel.folio", "Folio No")
    start_date = fields.Datetime(
        "Start Time", required=True, default=lambda self: fields.Datetime.now()
    )
    end_date = fields.Datetime("End Time", required=True)
    customer_id = fields.Many2one(
        "res.partner", "Customer Name", required=True
    )
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
        default="draft",
    )
    is_folio = fields.Boolean("Is a Hotel Guest??")

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        seq_obj = self.env["ir.sequence"]
        reserve = seq_obj.next_by_code("hotel.restaurant.reservation") or "New"
        vals["reservation_id"] = reserve
        return super(HotelRestaurantReservation, self).create(vals)

    @api.constrains("start_date", "end_date")
    def check_start_dates(self):
        """
        This method is used to validate the start_date and end_date.
        -------------------------------------------------------------
        @param self: object pointer
        @return: raise a warning depending on the validation
        """
        if self.start_date >= self.end_date:
            raise ValidationError(
                _("Start Date Should be less than the End Date!")
            )
        if self.is_folio is True:
            if self.start_date < self.folio_id.room_lines.checkin_date:
                raise ValidationError(
                    _(
                        "Start Date Should be greater than the Folio Check-in Date!"
                    )
                )
            if self.end_date > self.folio_id.room_lines.checkout_date:
                raise ValidationError(
                    _("End Date Should be less than the Folio Check-out Date!")
                )


class HotelRestaurantKitchenOrderTickets(models.Model):

    _name = "hotel.restaurant.kitchen.order.tickets"
    _description = "Includes Hotel Restaurant Order"
    _rec_name = "orderno"

    orderno = fields.Char("Order Number", readonly=True)
    resno = fields.Char("Reservation Number")
    kot_date = fields.Datetime("Date")
    room_no = fields.Char("Room No", readonly=True)
    w_name = fields.Char("Waiter Name", readonly=True)
    table_nos_ids = fields.Many2many(
        "hotel.restaurant.tables",
        "temp_table3",
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

    @api.depends("order_list_ids")
    def _compute_amount_all_total(self):
        """
        amount_subtotal and amount_total will display on change of order_list_ids
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        for sale in self:
            sale.amount_subtotal = sum(
                line.price_subtotal for line in sale.order_list_ids
            )
            if sale.amount_subtotal:
                sale.amount_total = (
                    sale.amount_subtotal
                    + (sale.amount_subtotal * sale.tax) / 100
                )

    @api.onchange("folio_id")
    def _onchange_folio_id(self):
        """
        When you change folio_id, based on that it will update
        the customer_id and room_number as well
        ---------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            self.customer_id = False
            self.room_id = False
            if rec.folio_id:
                self.customer_id = rec.folio_id.partner_id.id
                if rec.folio_id.room_lines:
                    self.room_id = rec.folio_id.room_lines[0].product_id.id

    def done_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel restaurant order
        ----------------------------------------
        @param self: object pointer
        """
        self.write({"state": "cancel"})

    def set_to_draft(self):
        """
        This method is used to change the state
        to draft of the hotel restaurant order
        ----------------------------------------
        @param self: object pointer
        """
        self.write({"state": "draft"})

    def generate_kot(self):
        """
        This method create new record for hotel restaurant order list.
        @param self: The object pointer
        @return: new record set for hotel restaurant order list.
        """
        res = []
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        restaurant_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            if len(order.order_list_ids.ids) == 0:
                raise ValidationError(_("Please Give an Order"))
            if len(order.table_nos_ids.ids) == 0:
                raise ValidationError(_("Please Assign a Table"))
            table_ids = [x.id for x in order.table_nos_ids]
            kot_data = order_tickets_obj.create(
                {
                    "orderno": order.order_no,
                    "kot_date": order.o_date,
                    "room_no": order.room_id.name,
                    "w_name": order.waiter_id.name,
                    "table_nos_ids": [(6, 0, table_ids)],
                }
            )
            self.kitchen_id = kot_data.id
            for order_line in order.order_list_ids:
                o_line = {
                    "kot_order_id": kot_data.id,
                    "menucard_id": order_line.menucard_id.id,
                    "item_qty": order_line.item_qty,
                    "item_rate": order_line.item_rate,
                }
                restaurant_order_list_obj.create(o_line)
                res.append(order_line.id)
            self.rest_item_id = [(6, 0, res)]
            self.state = "order"
        return True

    order_no = fields.Char("Order Number", readonly=True)
    o_date = fields.Datetime(
        "Order Date", required=True, default=lambda self: fields.Datetime.now()
    )
    room_id = fields.Many2one("product.product", "Room No")
    folio_id = fields.Many2one("hotel.folio", "Folio No")
    waiter_id = fields.Many2one("res.partner", "Waiter Name")
    table_nos_ids = fields.Many2many(
        "hotel.restaurant.tables",
        "temp_table2",
        "table_no",
        "name",
        "Table Number",
    )
    order_list_ids = fields.One2many(
        "hotel.restaurant.order.list", "restaurant_order_id", "Order List"
    )
    tax = fields.Float("Tax (%) ")
    amount_subtotal = fields.Float(
        compute="_compute_amount_all_total", string="Subtotal"
    )
    amount_total = fields.Float(
        compute="_compute_amount_all_total", string="Total"
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("order", "Order Created"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        "State",
        required=True,
        readonly=True,
        default="draft",
    )
    is_folio = fields.Boolean(
        "Is a Hotel Guest??", help="is customer reside" "in hotel or not"
    )
    customer_id = fields.Many2one(
        "res.partner", "Customer Name", required=True
    )
    kitchen_id = fields.Integer("Kitchen id")
    rest_item_id = fields.Many2many(
        "hotel.restaurant.order.list",
        "restau_kitc_ids",
        "restau_id",
        "kit_id",
        "Rest",
    )

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if self._context is None:
            self._context = {}
        seq_obj = self.env["ir.sequence"]
        rest_order = seq_obj.next_by_code("hotel.restaurant.order") or "New"
        vals["order_no"] = rest_order
        return super(HotelRestaurantOrder, self).create(vals)

    def generate_kot_update(self):
        """
        This method update record for hotel restaurant order list.
        ----------------------------------------------------------
        @param self: The object pointer
        @return: update record set for hotel restaurant order list.
        """
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        rest_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            line_data = {
                "orderno": order.order_no,
                "kot_date": time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "room_no": order.room_id.name,
                "w_name": order.waiter_id.name,
                "table_nos_ids": [(6, 0, order.table_nos_ids.ids)],
            }
            self.kitchen_id.write(line_data)
            for order_line in order.order_list_ids:
                if order_line.id not in order.rest_item_id.ids:
                    kot_data1 = order_tickets_obj.create(line_data)
                    order.kitchen_id = kot_data1.id
                    o_line = {
                        "kot_order_id": kot_data1.id,
                        "menucard_id": order_line.menucard_id.id,
                        "item_qty": order_line.item_qty,
                        "item_rate": order_line.item_rate,
                    }
                    order.rest_item_id = [(4, order_line.id)]
                    rest_order_list_obj.create(o_line)
        return True

    def done_order_kot(self):
        """
        This method is used to change the state
        to done of the hotel restaurant order
        ----------------------------------------
        @param self: object pointer
        """
        hsl_obj = self.env["hotel.service.line"]
        so_line_obj = self.env["sale.order.line"]
        for order_obj in self:
            if order_obj.folio_id:
                for order in order_obj.order_list_ids:
                    values = {
                        "order_id": order_obj.folio_id.order_id.id,
                        "name": order.name.name,
                        "product_id": order.name.product_id.id,
                        "product_uom": order.name.uom_id.id,
                        "product_uom_qty": order.item_qty,
                        "price_unit": order.item_rate,
                        "price_subtotal": order.price_subtotal,
                    }
                    sol_rec = so_line_obj.create(values)
                    hsl_obj.create(
                        {
                            "folio_id": order_obj.folio_id.id,
                            "service_line_id": sol_rec.id,
                        }
                    )
                    order_obj.folio_id.write(
                        {"hotel_restaurant_orders_ids": [(4, order_obj.id)]}
                    )
            self.write({"state": "done"})
        return True


class HotelReservationOrder(models.Model):

    _name = "hotel.reservation.order"
    _description = "Reservation Order"
    _rec_name = "order_number"

    @api.depends("order_list_ids")
    def _compute_amount_all_total(self):
        """
        amount_subtotal and amount_total will display on change of order_list_ids
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        for sale in self:
            sale.amount_subtotal = sum(
                line.price_subtotal for line in sale.order_list_ids
            )
            sale.amount_total = (
                sale.amount_subtotal + (sale.amount_subtotal * sale.tax) / 100
            )

    def reservation_generate_kot(self):
        """
        This method create new record for hotel restaurant order list.
        --------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel restaurant order list.
        """
        res = []
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        rest_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            if len(order.order_list_ids) == 0:
                raise ValidationError(_("Please Give an Order"))
            table_ids = [x.id for x in order.table_nos_ids]
            line_data = {
                "orderno": order.order_number,
                "resno": order.reservationno.reservation_id,
                "kot_date": order.order_date,
                "w_name": order.waitername.name,
                "table_nos_ids": [(6, 0, table_ids)],
            }
            kot_data = order_tickets_obj.create(line_data)
            self.kitchen_id = kot_data.id
            for order_line in order.order_list_ids:
                o_line = {
                    "kot_order_id": kot_data.id,
                    "menucard_id": order_line.menucard_id.id,
                    "item_qty": order_line.item_qty,
                    "item_rate": order_line.item_rate,
                }
                rest_order_list_obj.create(o_line)
                res.append(order_line.id)
            self.rests_ids = [(6, 0, res)]
            self.state = "order"
        return res

    def reservation_update_kot(self):
        """
        This method update record for hotel restaurant order list.
        ----------------------------------------------------------
        @param self: The object pointer
        @return: update record set for hotel restaurant order list.
        """
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        rest_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            table_ids = [x.id for x in order.table_nos_ids]
            line_data = {
                "orderno": order.order_number,
                "resno": order.reservationno.reservation_id,
                "kot_date": time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "w_name": order.waitername.name,
                "table_nos_ids": [(6, 0, table_ids)],
            }
            self.kitchen_id.write(line_data)
            for order_line in order.order_list_ids:
                if order_line not in order.rests_ids.ids:
                    kot_data1 = order_tickets_obj.create(line_data)
                    order.kitchen_id = kot_data1.id
                    o_line = {
                        "kot_order_id": kot_data1.id,
                        "menucard_id": order_line.menucard_id.id,
                        "item_qty": order_line.item_qty,
                        "item_rate": order_line.item_rate,
                    }
                    self.rests_ids = [(4, order_line.id)]
                    rest_order_list_obj.create(o_line)
        return True

    def done_kot(self):
        """
        This method is used to change the state
        to done of the hotel reservation order
        ----------------------------------------
        @param self: object pointer
        """
        hsl_obj = self.env["hotel.service.line"]
        so_line_obj = self.env["sale.order.line"]
        for order_obj in self:
            if order_obj.folio_id:
                for order in order_obj.order_list_ids:
                    values = {
                        "order_id": order_obj.folio_id.order_id.id,
                        "name": order.name.name,
                        "product_id": order.name.product_id.id,
                        "product_uom_qty": order.item_qty,
                        "price_unit": order.item_rate,
                        "price_subtotal": order.price_subtotal,
                    }
                    sol_rec = so_line_obj.create(values)
                    hsl_obj.create(
                        {
                            "folio_id": order_obj.folio_id.id,
                            "service_line_id": sol_rec.id,
                        }
                    )
                    order_obj.folio_id.write(
                        {"hotel_reservation_orders_ids": [(4, order_obj.id)]}
                    )
            if order_obj.reservationno:
                order_obj.reservationno.write({"state": "done"})
        self.write({"state": "done"})
        return True

    order_number = fields.Char("Order No", readonly=True)
    reservationno = fields.Many2one(
        "hotel.restaurant.reservation", "Reservation No"
    )
    order_date = fields.Datetime(
        "Date",
        required=True,
        default=(lambda *a: time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
    )
    waitername = fields.Many2one("res.partner", "Waiter Name")
    table_nos_ids = fields.Many2many(
        "hotel.restaurant.tables",
        "temp_table4",
        "table_no",
        "name",
        "Table Number",
    )
    order_list_ids = fields.One2many(
        "hotel.restaurant.order.list", "reservation_order_id", "Order List"
    )
    tax = fields.Float("Tax (%) ")
    amount_subtotal = fields.Float(
        compute="_compute_amount_all_total", string="Subtotal"
    )
    amount_total = fields.Float(
        compute="_compute_amount_all_total", string="Total"
    )
    kitchen_id = fields.Integer("Kitchen id")
    rests_ids = fields.Many2many(
        "hotel.restaurant.order.list",
        "reserv_id",
        "kitchen_id",
        "res_kit_ids",
        "Rest",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("order", "Order Created"), ("done", "Done")],
        "State",
        index=True,
        required=True,
        readonly=True,
        default="draft",
    )
    folio_id = fields.Many2one("hotel.folio", "Folio No")
    is_folio = fields.Boolean(
        "Is a Hotel Guest??", help="is customer reside" "in hotel or not"
    )

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if self._context is None:
            self._context = {}
        seq_obj = self.env["ir.sequence"]
        res_oder = seq_obj.next_by_code("hotel.reservation.order") or "New"
        vals["order_number"] = res_oder
        return super(HotelReservationOrder, self).create(vals)


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
            line.price_subtotal = line.item_rate * int(line.item_qty)

    @api.onchange("menucard_id")
    def _onchange_item_name(self):
        """
        item rate will display on change of item name
        ---------------------------------------------
        @param self: object pointer
        """
        if self.menucard_id:
            self.item_rate = self.menucard_id.list_price

    restaurant_order_id = fields.Many2one(
        "hotel.restaurant.order", "Restaurant Order"
    )
    reservation_order_id = fields.Many2one(
        "hotel.reservation.order", "Reservation Order"
    )
    kot_order_id = fields.Many2one(
        "hotel.restaurant.kitchen.order.tickets", "Kitchen Order Tickets"
    )
    menucard_id = fields.Many2one("hotel.menucard", "Item Name", required=True)
    item_qty = fields.Integer("Qty", required=True, default=1)
    item_rate = fields.Float("Rate")
    price_subtotal = fields.Float(
        compute="_compute_price_subtotal", method=True, string="Subtotal"
    )
