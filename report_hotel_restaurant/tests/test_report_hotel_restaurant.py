# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRestaurantSalesAnalysis(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.category = cls.env["hotel.menucard.type"].create({"name": "Analysis Food"})
        cls.dish = cls.env["hotel.menucard"].create(
            {
                "name": "Analysis Dish",
                "list_price": 50.0,
                "menu_card_categ_id": cls.category.id,
            }
        )
        cls.drink = cls.env["hotel.menucard"].create(
            {"name": "Analysis Drink", "list_price": 10.0}
        )
        cls.table = cls.env["hotel.restaurant.tables"].create({"name": "AN-T1"})
        cls.customer = cls.env["res.partner"].create({"name": "Analysis Customer"})
        cls.waiter = cls.env["res.partner"].create({"name": "Analysis Waiter"})
        cls.Report = cls.env["report.hotel.restaurant.status"]

    def _lines(self, *items):
        return [
            Command.create({"menucard_id": item.id, "item_qty": qty, "item_rate": rate})
            for item, qty, rate in items
        ]

    def _table_order(self, *items):
        return self.env["hotel.restaurant.order"].create(
            {
                "customer_id": self.customer.id,
                "waiter_id": self.waiter.id,
                "table_nos_ids": [Command.set(self.table.ids)],
                "order_list_ids": self._lines(*items),
            }
        )

    def _booking_order(self, *items):
        now = fields.Datetime.now()
        booking = self.env["hotel.restaurant.reservation"].create(
            {
                "customer_id": self.customer.id,
                "start_date": now + timedelta(days=1),
                "end_date": now + timedelta(days=1, hours=2),
                "table_nos_ids": [Command.set(self.table.ids)],
            }
        )
        booking.table_reserved()
        booking.create_order()
        order = self.env["hotel.reservation.order"].search(
            [("reservation_id", "=", booking.id)]
        )
        order.order_list_ids = self._lines(*items)
        return order

    def _rows(self, numbers):
        self.env.flush_all()
        return self.Report.search([("order_number", "in", numbers)])

    def test_table_order_lines(self):
        order = self._table_order((self.dish, 2, 50.0), (self.drink, 3, 10.0))
        rows = self._rows([order.order_no])
        self.assertEqual(len(rows), 2)
        self.assertEqual(set(rows.mapped("order_kind")), {"table"})
        self.assertEqual(rows.menucard_id, self.dish | self.drink)
        self.assertEqual(sum(rows.mapped("quantity")), 5)
        self.assertEqual(sum(rows.mapped("amount")), 130.0)
        # the order is counted once, whatever the number of lines
        self.assertEqual(sum(rows.mapped("no_of_reservation_order")), 1)
        dish_row = rows.filtered(lambda r: r.menucard_id == self.dish)
        self.assertEqual(dish_row.menu_categ_id, self.category)
        self.assertEqual(dish_row.customer_id, self.customer)
        self.assertEqual(dish_row.waiter_id, self.waiter)

    def test_booking_order_lines(self):
        order = self._booking_order((self.dish, 1, 50.0))
        row = self._rows([order.order_number])
        self.assertEqual(row.order_kind, "booking")
        self.assertEqual(row.reservation_id, order.reservation_id.reservation_id)
        self.assertEqual(row.customer_id, self.customer)
        self.assertEqual(row.amount, 50.0)

    def test_kitchen_tickets_not_counted(self):
        order = self._table_order((self.dish, 2, 50.0))
        order.generate_kot()
        rows = self._rows([order.order_no])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.quantity, 2)
        self.assertEqual(rows.state, "order")

    def test_order_without_lines_and_cancel(self):
        empty = self._table_order()
        cancelled = self._table_order((self.drink, 1, 10.0))
        cancelled.done_cancel()
        rows = self._rows([empty.order_no, cancelled.order_no])
        empty_row = rows.filtered(lambda r: r.order_number == empty.order_no)
        self.assertEqual(
            (empty_row.quantity, empty_row.amount, empty_row.no_of_reservation_order),
            (0, 0.0, 1),
        )
        not_cancelled = self.Report.search(
            [
                ("order_number", "in", [empty.order_no, cancelled.order_no]),
                ("state", "!=", "cancel"),
            ]
        )
        self.assertEqual(not_cancelled.mapped("order_number"), [empty.order_no])

    def test_group_by_category(self):
        first = self._table_order((self.dish, 2, 50.0))
        second = self._booking_order((self.dish, 1, 50.0), (self.drink, 4, 10.0))
        self.env.flush_all()
        groups = {
            category: (quantity, amount)
            for category, quantity, amount in self.Report._read_group(
                [("order_number", "in", [first.order_no, second.order_number])],
                ["menu_categ_id"],
                ["quantity:sum", "amount:sum"],
            )
        }
        self.assertEqual(groups[self.category], (3, 150.0))
