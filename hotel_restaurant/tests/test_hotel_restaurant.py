# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, time, timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Command
from odoo.tests import TransactionCase, new_test_user, tagged

from ..models.hotel_restaurant import _room_product_domain


@tagged("post_install", "-at_install")
class TestRestaurant(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.env.company.external_report_layout_id = cls.env.ref(
            "web.external_layout_standard"
        )
        MenuType = cls.env["hotel.menucard.type"]
        cls.root_type = MenuType.create({"name": "Test Menu Root"})
        cls.punjabi = MenuType.create(
            {"name": "Test Punjabi", "menu_id": cls.root_type.id}
        )
        cls.dish = cls.env["hotel.menucard"].create(
            {
                "name": "Malai Kofta",
                "list_price": 100.0,
                "menu_card_categ_id": cls.punjabi.id,
            }
        )
        cls.dish2 = cls.env["hotel.menucard"].create(
            {"name": "Tandoori Roti", "list_price": 20.0}
        )
        Table = cls.env["hotel.restaurant.tables"]
        cls.table1 = Table.create({"name": "T-1", "capacity": 2})
        cls.table2 = Table.create({"name": "T-2", "capacity": 4})
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.waiter = cls.env["res.partner"].create({"name": "Test Waiter"})
        room_type = cls.env["hotel.room.type"].create({"name": "Restaurant Test Type"})
        cls.room = cls.env["hotel.room"].create(
            {"name": "R-101", "capacity": 2, "room_categ_id": room_type.id}
        )
        cls.base = datetime.combine(fields.Date.today() + timedelta(days=5), time(12))
        cls.folio = cls.env["hotel.folio"].create(
            {
                "partner_id": cls.partner.id,
                "checkin_date": cls.base - timedelta(days=1),
                "checkout_date": cls.base + timedelta(days=2),
                "room_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.room.product_id.id,
                            "checkin_date": cls.base - timedelta(days=1),
                            "checkout_date": cls.base + timedelta(days=2),
                            "product_uom_qty": 3,
                        }
                    )
                ],
            }
        )
        cls.hotel_user = new_test_user(
            cls.env,
            login="restaurant_user",
            groups="base.group_user,vertical_hotel.group_hotel_user",
        )

    def _booking(self, tables=None, start=0, hours=2, **vals):
        values = {
            "customer_id": self.partner.id,
            "start_date": self.base + timedelta(hours=start),
            "end_date": self.base + timedelta(hours=start + hours),
            "table_nos_ids": [Command.set((tables or self.table1).ids)],
        }
        values.update(vals)
        return self.env["hotel.restaurant.reservation"].create(values)

    def _order(self, **vals):
        values = {
            "customer_id": self.partner.id,
            "waiter_id": self.waiter.id,
            "table_nos_ids": [Command.set(self.table1.ids)],
            "order_list_ids": [
                Command.create(
                    {"menucard_id": self.dish.id, "item_qty": 2, "item_rate": 100.0}
                )
            ],
        }
        values.update(vals)
        return self.env["hotel.restaurant.order"].create(values)

    def _kots(self, number):
        return self.env["hotel.restaurant.kitchen.order.tickets"].search(
            [("order_number", "=", number)]
        )

    def _render(self, report_xmlid, docids, data=None):
        report = self.env.ref(report_xmlid)
        return (
            self.env["ir.actions.report"]
            ._render_qweb_html(report.report_name, docids, data=data)[0]
            .decode()
        )

    # Food categories

    def test_name_search(self):
        self.assertEqual(self.punjabi.display_name, "Test Menu Root / Test Punjabi")
        found = self.env["hotel.menucard.type"].name_search(
            "Test Menu Root / Test Punjabi"
        )
        self.assertEqual([res[0] for res in found], self.punjabi.ids)

    def test_menu_type_cycle(self):
        with self.assertRaises(ValidationError):
            self.root_type.menu_id = self.punjabi

    # Table bookings

    def test_booking_workflow(self):
        booking = self._booking()
        self.assertTrue(booking.reservation_id)
        booking.table_reserved()
        self.assertEqual(booking.state, "confirm")
        booking.table_done()
        booking.create_order()
        self.assertEqual(booking.state, "order")
        order = self.env["hotel.reservation.order"].search(
            [("reservation_id", "=", booking.id)]
        )
        self.assertEqual(order.table_nos_ids, self.table1)
        with self.assertRaises(UserError):
            booking.table_reserved()

    def test_booking_overlap(self):
        self._booking().table_reserved()
        with self.assertRaises(ValidationError):
            self._booking(start=1).table_reserved()
        # another table, or right after: fine
        self._booking(tables=self.table2, start=1).table_reserved()
        self._booking(start=2).table_reserved()

    def test_cancelled_booking_frees_tables(self):
        cancelled = self._booking()
        cancelled.table_reserved()
        cancelled.table_cancel()
        other = self._booking()
        other.table_reserved()
        self.assertEqual(other.state, "confirm")
        cancelled.action_set_to_draft()
        self.assertEqual(cancelled.state, "draft")

    def test_booking_dates(self):
        with self.assertRaises(ValidationError):
            self._booking(hours=-1)
        first, second = self._booking(), self._booking(start=5)
        (first | second).write({"end_date": self.base + timedelta(hours=10)})
        with self.assertRaises(ValidationError):
            self._booking(is_folio=True, folio_id=self.folio.id, start=24 * 5)

    def test_room_domain(self):
        rooms = self.env["product.product"].search(
            _room_product_domain(self.env["hotel.restaurant.order"])
        )
        self.assertIn(self.room.product_id, rooms)
        self.assertNotIn(self.dish.product_id, rooms)

    # Kitchen order tickets

    def test_order_kot(self):
        order = self._order()
        self.assertEqual(order.amount_subtotal, 200.0)
        order.tax = 10
        self.assertAlmostEqual(order.amount_total, 220.0)
        order.generate_kot()
        self.assertEqual(order.state, "order")
        kot = self._kots(order.order_no)
        self.assertEqual(len(kot), 1)
        self.assertEqual(kot.kot_list_ids.menucard_id, self.dish)
        # nothing new: no new ticket
        order.generate_kot_update()
        self.assertEqual(len(self._kots(order.order_no)), 1)
        # one new line: one ticket with that line only
        order.order_list_ids = [
            Command.create(
                {"menucard_id": self.dish2.id, "item_qty": 1, "item_rate": 20}
            )
        ]
        order.generate_kot_update()
        kots = self._kots(order.order_no)
        self.assertEqual(len(kots), 2)
        self.assertEqual((kots - kot).kot_list_ids.menucard_id, self.dish2)
        with self.assertRaises(UserError):
            order.generate_kot()

    def test_reservation_order_kot(self):
        booking = self._booking()
        booking.table_reserved()
        booking.table_done()
        booking.create_order()
        order = self.env["hotel.reservation.order"].search(
            [("reservation_id", "=", booking.id)]
        )
        order.order_list_ids = [
            Command.create(
                {"menucard_id": self.dish.id, "item_qty": 1, "item_rate": 100}
            )
        ]
        order.reservation_generate_kot()
        self.assertEqual(len(self._kots(order.order_number)), 1)
        order.reservation_update_kot()
        self.assertEqual(len(self._kots(order.order_number)), 1)
        order.order_list_ids = [
            Command.create(
                {"menucard_id": self.dish2.id, "item_qty": 2, "item_rate": 20}
            )
        ]
        order.reservation_update_kot()
        self.assertEqual(len(self._kots(order.order_number)), 2)

    # Charging the folio

    def test_charge_folio_once(self):
        order = self._order(folio_id=self.folio.id, is_folio=True)
        order.generate_kot()
        lines_before = len(self.folio.order_id.order_line)
        order.done_order_kot()
        self.assertEqual(order.state, "done")
        new_lines = self.folio.order_id.order_line[lines_before:]
        self.assertEqual(new_lines.product_id, self.dish.product_id)
        self.assertEqual(new_lines.product_uom_qty, 2)
        self.assertEqual(new_lines.price_unit, 100.0)
        self.assertIn(order, self.folio.hotel_restaurant_orders_ids)
        with self.assertRaises(UserError):
            order.done_order_kot()
        with self.assertRaises(UserError):
            order.done_cancel()
        self.assertEqual(len(self.folio.order_id.order_line), lines_before + 1)

    def test_done_without_folio(self):
        order = self._order()
        with self.assertRaises(UserError):
            order.done_order_kot()
        order.generate_kot()
        order.done_order_kot()
        self.assertEqual(order.state, "done")

    def test_cancel_and_draft(self):
        order = self._order()
        order.done_cancel()
        self.assertEqual(order.state, "cancel")
        order.set_to_draft()
        self.assertEqual(order.state, "draft")

    def test_reservation_order_charge(self):
        booking = self._booking(folio_id=self.folio.id, is_folio=True)
        booking.table_reserved()
        booking.create_order()
        order = self.env["hotel.reservation.order"].search(
            [("reservation_id", "=", booking.id)]
        )
        order.order_list_ids = [
            Command.create(
                {"menucard_id": self.dish.id, "item_qty": 1, "item_rate": 100}
            )
        ]
        order.reservation_generate_kot()
        order.done_kot()
        self.assertEqual(booking.state, "done")
        self.assertIn(order, self.folio.hotel_reservation_orders_ids)
        with self.assertRaises(UserError):
            order.done_kot()

    # Reports

    def test_kot_and_bill_reports(self):
        order = self._order(folio_id=self.folio.id, room_id=self.room.product_id.id)
        html = self._render("hotel_restaurant.report_hotel_res_order_kot", order.ids)
        self.assertIn(order.order_no, html)
        self.assertIn("Malai Kofta", html)
        self.assertIn("T-1", html)
        html = self._render("hotel_restaurant.report_hotel_res_order_bill", order.ids)
        self.assertIn(order.order_no, html)
        self.assertIn("Malai Kofta", html)
        self.assertIn("200.00", html)

    def test_reservation_bill(self):
        booking = self._booking()
        booking.table_reserved()
        booking.create_order()
        order = self.env["hotel.reservation.order"].search(
            [("reservation_id", "=", booking.id)]
        )
        order.order_list_ids = [
            Command.create(
                {"menucard_id": self.dish2.id, "item_qty": 3, "item_rate": 20}
            )
        ]
        html = self._render(
            "hotel_restaurant.report_hotel_reservation_order_bill", order.ids
        )
        self.assertIn(order.order_number, html)
        self.assertIn("60.00", html)

    def test_table_list_report(self):
        booking = self._booking()
        cancelled = self._booking(tables=self.table2)
        cancelled.table_cancel()
        wizard = self.env["wizard.hotel.restaurant"].create(
            {
                "date_start": self.base - timedelta(days=1),
                "date_end": self.base + timedelta(days=1),
            }
        )
        action = wizard.print_report()
        html = self._render(
            "hotel_restaurant.report_hotel_table_res", wizard.ids, action["data"]
        )
        self.assertIn(booking.reservation_id, html)
        self.assertNotIn(cancelled.reservation_id, html)
        self.assertIn("<h2", html)
        later = {
            "form": {
                "date_start": "2099-01-01 00:00:00",
                "date_end": "2099-01-31 00:00:00",
            }
        }
        html = self._render(
            "hotel_restaurant.report_hotel_table_res", wizard.ids, later
        )
        self.assertNotIn(booking.reservation_id, html)
        self.assertIn("No reservation in this period.", html)

    def test_folio_reports(self):
        order = self._order(folio_id=self.folio.id, is_folio=True)
        order.generate_kot()
        order.done_order_kot()
        wizard = self.env["folio.rest.reservation"].create(
            {
                "date_start": self.base - timedelta(days=10),
                "date_end": self.base + timedelta(days=10),
                "check": True,
            }
        )
        action = wizard.print_reserv_report()
        html = self._render(
            "hotel_restaurant.report_hotel_res_folio1", wizard.ids, action["data"]
        )
        self.assertIn(self.folio.display_name, html)
        self.assertIn(order.order_no, html)
        self.assertIn("200.00", html)
        action = wizard.print_rest_report()
        html = self._render(
            "hotel_restaurant.report_hotel_res_folio", wizard.ids, action["data"]
        )
        self.assertIn("No restaurant order in this period.", html)

    # Access

    def test_hotel_user_access(self):
        booking = self._booking().with_user(self.hotel_user)
        booking.table_reserved()
        order = self._order().with_user(self.hotel_user)
        order.generate_kot()
        with self.assertRaises(AccessError):
            booking.unlink()
