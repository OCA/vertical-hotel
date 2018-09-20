# See LICENSE file for full copyright and licensing details.

from odoo.tests import common
from datetime import datetime


class TestRestaurant(common.TransactionCase):

    def setUp(self):
        super(TestRestaurant, self).setUp()
        self.menucard_type_obj = self.env['hotel.menucard.type']
        self.hotel_rest_reserv_obj = self.env['hotel.restaurant.reservation']
        self.hotel_kot_obj = self.\
            env['hotel.restaurant.kitchen.order.tickets']
        self.rest_order_obj = self.env['hotel.restaurant.order.list']
        self.hotel_rest_order_obj = self.env['hotel.restaurant.order']
        self.hotel_reserv_order_obj = self.env['hotel.reservation.order']
        self.fooditem = self.env.ref('hotel_restaurant.hotel_fooditem_5')
        self.fooditem_type = self.env.\
            ref('hotel_restaurant.hotel_menucard_type_1')
        self.rest_res = self.env.\
            ref('hotel_restaurant.hotel_restaurant_reservation_1')
        self.tablelist = self.env.\
            ref('hotel_restaurant.hotel_reservation_order_line_0')
        self.table1 = self.env.\
            ref('hotel_restaurant.hotel_restaurant_tables_table1')
        self.table0 = self.env.\
            ref('hotel_restaurant.hotel_restaurant_tables_table0')
        self.room1 = self.env.ref('point_of_sale.partner_product_3')
        self.partner = self.env.ref('base.res_partner_4')
        self.waiter = self.env.ref('base.res_partner_3')
        cur_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.menucard_type = self.menucard_type_obj.\
            create({'name': 'Punjabi',
                    'menu_id': self.fooditem_type.id,
                    })

        self.menucard_type.name_get()
        hotel_menucard_type = self.menucard_type.name_search('Punjabi')
        self.assertEqual(len(hotel_menucard_type), 2,
                         'Incorrect search number result for name_search')

        self.hotel_rest_order = self.hotel_rest_order_obj.\
            create({'cname': self.partner.id,
                    'room_no': self.room1.id,
                    'amount_subtotal': 500.00,
                    'amount_total': 500.00,
                    'waiter_name': self.waiter.id,
                    'table_no': [(6, 0, [self.table1.id, self.table0.id])],
                    'kitchen_id': 1,
                    'state': 'draft',
                    'order_list': [(6, 0, [self.tablelist.id])],
                    })

        self.rest_order = self.rest_order_obj.\
            create({'name': self.fooditem.id,
                    'price_subtotal': 500.00,
                    'item_qty': 2,
                    'item_rate': 1000.00,
                    })

        self.hotel_reserv_order = self.hotel_reserv_order_obj.\
            create({'order_number': '0RR/00001',
                    'reservationno': self.rest_res.id,
                    'order_date': cur_date,
                    'waitername': self.waiter.id,
                    'amount_subtotal': 500.00,
                    'amount_total': 500.00,
                    'rest_id': [(6, 0, [self.tablelist.id])],
                    'table_no': [(6, 0, [self.table1.id, self.table0.id])],
                    'kitchen_id': 1,
                    'state': 'draft',
                    'order_list': [(6, 0, [self.tablelist.id])],
                    })

    def test_compute_price_subtotal(self):
        self.rest_order._compute_price_subtotal()

    def test_on_change_item_name(self):
        self.rest_order.on_change_item_name()

    def test_compute_amount_all_total_reserv(self):
        self.hotel_reserv_order._compute_amount_all_total()

    def test_reservation_generate_kot(self):
        self.hotel_reserv_order.reservation_generate_kot()
        self.assertEqual(self.hotel_reserv_order.state == 'order', True)

    def test_done_kot(self):
        self.hotel_reserv_order.done_kot()
        self.assertEqual(self.hotel_reserv_order.state == 'done', True)

    def test_compute_amount_all_total_rest(self):
        self.hotel_rest_order._compute_amount_all_total()

    def test_done_cancel(self):
        self.hotel_rest_order.done_cancel()
        self.assertEqual(self.hotel_rest_order.state == 'cancel', True)

    def test_set_to_draft(self):
        self.hotel_rest_order.set_to_draft()
        self.assertEqual(self.hotel_rest_order.state == 'draft', True)

    def test_generate_kot(self):
        self.assertEqual(len(self.tablelist.ids), 1, 'Please Give an Order')
        self.hotel_rest_order.generate_kot()
        self.assertEqual(self.hotel_rest_order.state == 'order', True)

    def test_done_order_kot(self):
        self.hotel_rest_order.done_order_kot()
        self.assertEqual(self.hotel_rest_order.state == 'done', True)
