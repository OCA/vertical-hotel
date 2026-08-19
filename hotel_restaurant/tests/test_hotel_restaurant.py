# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.tests import common


class TestRestaurant(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.menucard_type_obj = self.env["hotel.menucard.type"]
        self.hotel_rest_reserv_obj = self.env["hotel.restaurant.reservation"]
        self.hotel_kot_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        self.rest_order_obj = self.env["hotel.restaurant.order.list"]
        self.hotel_rest_order_obj = self.env["hotel.restaurant.order"]
        self.hotel_reserv_order_obj = self.env["hotel.reservation.order"]
        self.root_fooditem_type = self.menucard_type_obj.create(
            {"name": "All FoodItems"}
        )
        self.fooditem_type = self.menucard_type_obj.create(
            {"name": "Punjabi", "menu_id": self.root_fooditem_type.id}
        )
        self.fooditem = self.env["hotel.menucard"].create(
            {
                "name": "Malai Kofta",
                "list_price": 1000.00,
                "menu_card_categ_id": self.fooditem_type.id,
            }
        )
        self.table0 = self.env["hotel.restaurant.tables"].create(
            {"name": "Table-1", "capacity": 2}
        )
        self.table1 = self.env["hotel.restaurant.tables"].create(
            {"name": "Table-2", "capacity": 4}
        )
        self.room1 = self.env["product.product"].create({"name": "Room 101"})
        self.partner = self.env["res.partner"].create({"name": "Test Customer"})
        self.waiter = self.env["res.partner"].create({"name": "Test Waiter"})
        self.menucard_type_1 = self.env["hotel.menucard.type"]
        cur_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.rest_res = self.hotel_rest_reserv_obj.create(
            {
                "customer_id": self.partner.id,
                "room_id": self.room1.id,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=1),
                "table_nos_ids": [(6, 0, [self.table1.id, self.table0.id])],
            }
        )
        self.tablelist = self.rest_order_obj.create(
            {
                "menucard_id": self.fooditem.id,
                "item_qty": 1,
                "item_rate": 1000.00,
            }
        )

        self.menucard_type = self.menucard_type_obj.create(
            {"name": "Punjabi", "menu_id": self.fooditem_type.id}
        )

        self.menucard_type.mapped("display_name")
        hotel_menucard_type = self.menucard_type.name_search("Punjabi")
        self.assertEqual(
            len(hotel_menucard_type),
            2,
            "Incorrect search number result for name_search",
        )

        self.hotel_rest_order = self.hotel_rest_order_obj.create(
            {
                "customer_id": self.partner.id,
                "room_id": self.room1.id,
                "amount_subtotal": 500.00,
                "amount_total": 500.00,
                "waiter_id": self.waiter.id,
                "table_nos_ids": [(6, 0, [self.table1.id, self.table0.id])],
                "kitchen": 1,
                "state": "draft",
                "order_list_ids": [(6, 0, [self.tablelist.id])],
            }
        )

        self.rest_order = self.rest_order_obj.create(
            {
                "menucard_id": self.fooditem.id,
                "price_subtotal": 500.00,
                "item_qty": 2,
                "item_rate": 1000.00,
            }
        )

        self.hotel_reserv_order = self.hotel_reserv_order_obj.create(
            {
                "order_number": "0RR/00001",
                "reservation_id": self.rest_res.id,
                "order_date": cur_date,
                "waiter_id": self.waiter.id,
                "amount_subtotal": 500.00,
                "amount_total": 500.00,
                "rests_ids": [(6, 0, [self.tablelist.id])],
                "table_nos_ids": [(6, 0, [self.table1.id, self.table0.id])],
                "kitchen": 1,
                "state": "draft",
                "order_list_ids": [(6, 0, [self.tablelist.id])],
            }
        )

    def test_name_search(self):
        self.menucard_type_1 = self.env["hotel.menucard.type"].create(
            {
                "name": "Test",
            }
        )
        self.env["hotel.menucard.type"].name_search(
            "All FoodItems / Punjabi", [], "not like", None
        )

    def test_compute_price_subtotal(self):
        self.rest_order._compute_price_subtotal()

    def test_on_change_item_name(self):
        self.rest_order._onchange_item_name()

    def test_compute_amount_all_total_reserv(self):
        self.hotel_reserv_order._compute_amount_all_total()

    def test_reservation_generate_kot(self):
        self.hotel_reserv_order.reservation_generate_kot()
        self.assertEqual(self.hotel_reserv_order.state == "order", True)

    def test_done_kot(self):
        self.hotel_reserv_order.done_kot()
        self.assertEqual(self.hotel_reserv_order.state == "done", True)

    def test_compute_amount_all_total_rest(self):
        self.hotel_rest_order._compute_amount_all_total()

    def test_done_cancel(self):
        self.hotel_rest_order.done_cancel()
        self.assertEqual(self.hotel_rest_order.state == "cancel", True)

    def test_set_to_draft(self):
        self.hotel_rest_order.set_to_draft()
        self.assertEqual(self.hotel_rest_order.state == "draft", True)

    def test_generate_kot(self):
        self.assertEqual(len(self.tablelist.ids), 1, "Please Give an Order")
        self.hotel_rest_order.generate_kot()
        self.assertEqual(self.hotel_rest_order.state == "order", True)

    def test_done_order_kot(self):
        self.hotel_rest_order.done_order_kot()
        self.assertEqual(self.hotel_rest_order.state == "done", True)
