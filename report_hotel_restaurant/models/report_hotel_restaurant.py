# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools
from odoo.tools import SQL


class ReportHotelRestaurantStatus(models.Model):
    """Restaurant sales analysis: one row per order line, for the table
    orders (hotel.restaurant.order) and the orders of table bookings
    (hotel.reservation.order). Kitchen order ticket lines are copies and
    are left out.

    The order counter is only on the first row of each order, so its sum
    is the number of orders; an order without lines keeps one row."""

    _name = "report.hotel.restaurant.status"
    _description = "Restaurant Sales Analysis"
    _auto = False
    _order = "order_date desc, order_number desc"

    order_kind = fields.Selection(
        [("table", "Table Order"), ("booking", "Booking Order")],
        readonly=True,
    )
    order_number = fields.Char(readonly=True)
    order_date = fields.Datetime(readonly=True)
    reservation_id = fields.Char("Reservation No", readonly=True)
    customer_id = fields.Many2one("res.partner", readonly=True)
    waiter_id = fields.Many2one("res.partner", readonly=True)
    folio_id = fields.Many2one("hotel.folio", readonly=True)
    is_folio = fields.Boolean("Hotel Guest", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("order", "Order Created"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        readonly=True,
    )
    menucard_id = fields.Many2one("hotel.menucard", "Food Item", readonly=True)
    menu_categ_id = fields.Many2one(
        "hotel.menucard.type", "Food Item Category", readonly=True
    )
    quantity = fields.Integer(readonly=True)
    amount = fields.Float(readonly=True)
    no_of_reservation_order = fields.Integer("Orders", readonly=True)

    def init(self):
        """
        Initialization for report hotel restaurant status module.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                WITH order_lines AS (
                    SELECT
                        'table' AS order_kind,
                        o.id AS order_id,
                        o.order_no AS order_number,
                        o.o_date AS order_date,
                        NULL::varchar AS reservation_id,
                        o.customer_id,
                        o.waiter_id,
                        o.folio_id,
                        o.is_folio,
                        o.state,
                        line.id AS line_id,
                        line.menucard_id,
                        line.item_qty,
                        line.item_rate
                    FROM hotel_restaurant_order o
                    LEFT JOIN hotel_restaurant_order_list line
                        ON line.restaurant_order_id = o.id
                    UNION ALL
                    SELECT
                        'booking' AS order_kind,
                        o.id AS order_id,
                        o.order_number,
                        o.order_date,
                        booking.reservation_id,
                        booking.customer_id,
                        o.waiter_id,
                        o.folio_id,
                        o.is_folio,
                        o.state,
                        line.id AS line_id,
                        line.menucard_id,
                        line.item_qty,
                        line.item_rate
                    FROM hotel_reservation_order o
                    LEFT JOIN hotel_restaurant_reservation booking
                        ON booking.id = o.reservation_id
                    LEFT JOIN hotel_restaurant_order_list line
                        ON line.reservation_order_id = o.id
                )
                SELECT
                    row_number() OVER (
                        ORDER BY ol.order_kind, ol.order_id, ol.line_id
                    ) AS id,
                    ol.order_kind,
                    ol.order_number,
                    ol.order_date,
                    ol.reservation_id,
                    ol.customer_id,
                    ol.waiter_id,
                    ol.folio_id,
                    COALESCE(ol.is_folio, false) AS is_folio,
                    ol.state,
                    ol.menucard_id,
                    menu.menu_card_categ_id AS menu_categ_id,
                    COALESCE(ol.item_qty, 0) AS quantity,
                    COALESCE(ol.item_qty, 0) * COALESCE(ol.item_rate, 0) AS amount,
                    CASE WHEN row_number() OVER (
                        PARTITION BY ol.order_kind, ol.order_id ORDER BY ol.line_id
                    ) = 1 THEN 1 ELSE 0 END AS no_of_reservation_order
                FROM order_lines ol
                LEFT JOIN hotel_menucard menu ON menu.id = ol.menucard_id
            )"""
        self.env.cr.execute(SQL(query, SQL.identifier(self._table)))
