# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo.tests import common
from datetime import datetime
from odoo.exceptions import ValidationError, UserError


class TestHotel(common.TransactionCase):

    def setUp(self):
        super(TestHotel, self).setUp()
        self.room_type_obj = self.env['hotel.room.type']
        self.amenities_type_obj = self.env['hotel.room.amenities.type']
        self.hotel_room_obj = self.env['hotel.room']
        self.hotel_folio_obj = self.env['hotel.folio']
        self.hotel_service_type_obj = self.env['hotel.service.type']
        self.currency_exchange_obj = self.env['currency.exchange']
        self.hotel_room_type = self.env.ref('hotel.rooms')
        self.hroom = self.env.ref('hotel.hotel_room_0')
        self.amenity_type = self.env.ref('hotel.hotel_room_amenities_type_0')
        self.room = self.env.ref('point_of_sale.partner_product_3')
        self.floor = self.env.ref('hotel.hotel_floor_ground0')
        self.manager = self.env.ref('base.user_root')
        self.partner = self.env.ref('base.res_partner_2')
        self.partner1 = self.env.ref('base.res_partner_3')
        self.pricelist = self.env.ref('product.list0')
        self.warehouse = self.env.ref('stock.warehouse0')
        self.service_type = self.env.ref('hotel.hotel_service_type_1')
        self.currency_eur = self.env.ref('base.EUR')
        self.currency_inr = self.env.ref('base.INR')
        cur_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.room_type = self.room_type_obj.\
            create({'name': 'Single 101',
                    'categ_id': self.hotel_room_type.id,
                    })

        self.amenities_type = self.amenities_type_obj.\
            create({'name': 'Beds',
                    'amenity_id': self.amenity_type.id,
                    })

        self.hotel_room = self.hotel_room_obj.\
            create({'product_id': self.room.id,
                    'floor_id': self.floor.id,
                    'max_adult': 2,
                    'max_child': 1,
                    'categ_id': self.room_type.id,
                    'capacity': 4,
                    'status': 'available',
                    'product_manager': self.manager.id,
                    })

        self.hotel_folio = self.hotel_folio_obj.\
            create({'name': 'Folio/00001',
                    'checkin_date': cur_date,
                    'checkout_date': cur_date,
                    'partner_id': self.partner.id,
                    'pricelist_id': self.pricelist.id,
                    'warehouse_id': self.warehouse.id,
                    })

        self.hotel_service_type = self.hotel_service_type_obj.\
            create({'name': 'Fixed',
                    'service_id': self.service_type.id,
                    })

        self.currency_exchange = self.currency_exchange_obj.\
            create({'today_date': cur_date,
                    'input_curr': self.currency_eur.id,
                    'out_curr': self.currency_inr.id,
                    'in_amount': 1.00,
                    'folio_no': self.hotel_folio.id,
                    'guest_name': self.partner.id,
                    'room_number': 'Single 101',
                    'state': 'draft',
                    'rate': 75.34,
                    'hotel_id': self.warehouse.id,
                    'type': 'cash',
                    'tax': '2',
                    'total': 76.85,
                    })

        account_obj = self.env['account.account']
        acc_payable = self.env.ref('account.data_account_type_payable')
        direct_cost = self.env.ref('account.data_account_type_direct_costs')
        inv_partner = self.env.ref('base.res_partner_2')
        company = self.env.ref('base.main_company')
        journal = self.env['account.journal'].\
            create({'name': 'Purchase Journal - Test', 'code': 'STPJ',
                    'type': 'purchase', 'company_id': company.id})
        account_payable = account_obj.create({'code': 'X1111',
                                              'name': 'Sale - Test\
                                              Payable Account',
                                              'user_type_id': acc_payable.id,
                                              'reconcile': True})
        account_income = account_obj.create({'code': 'X1112',
                                             'name': 'Sale - Test Account',
                                             'user_type_id': direct_cost.id})
        invoice_vals = {
            'name': '',
            'type': 'in_invoice',
            'partner_id': inv_partner.id,
            'invoice_line_ids': [(0, 0,
                                  {'name': self.room.name,
                                   'product_id': self.room.id,
                                   'quantity': 2,
                                   'uom_id': self.room.uom_id.id,
                                   'price_unit': self.room.standard_price,
                                   'account_id': account_income.id})],
            'account_id': account_payable.id,
            'journal_id': journal.id,
            'currency_id': company.currency_id.id,
        }
        self.env['account.invoice'].create(invoice_vals)

    def test_room_type_name_get(self):
        self.room_type.name_get()

    def test_room_type_name_search(self):
        h_room_type = self.room_type.name_search('Single 101')
        self.assertEqual(len(h_room_type), 1,
                         'Incorrect search number result for name_search')

    def test_amenity_type_name_get(self):
        self.amenities_type.name_get()

    def test_amenity_type_name_search(self):
        hotel_amenity_type = self.amenities_type.name_search('Beds')
        self.assertEqual(len(hotel_amenity_type), 2,
                         'Incorrect search number result for name_search')

    def test_check_capacity(self):
        self.hotel_room.check_capacity()

    def test_isroom_change(self):
        self.hotel_room.isroom_change()

    def test_set_room_status_occupied(self):
        self.hotel_room.set_room_status_occupied()

    def test_set_room_status_available(self):
        self.hotel_room.set_room_status_available()

    def test_folio_name_get(self):
        self.hotel_folio.name_get()

    def test_folio_needaction_count(self):
        self.hotel_folio._needaction_count()
        self.assertEqual(self.hotel_folio.state == 'draft', True)

    def test_folio_get_checkin_date(self):
        self.hotel_folio._get_checkin_date()

    def test_folio_get_checkout_date(self):
        self.hotel_folio._get_checkout_date()

    def test_folio_copy(self):
        self.hotel_folio.copy()

    def test_go_to_currency_exchange(self):
        with self.assertRaises(ValidationError):
            self.hotel_folio.go_to_currency_exchange()

    def test_folio_room_lines(self):
        self.hotel_folio.folio_room_lines()

    def test_onchange_dates(self):
        self.hotel_folio.onchange_dates()

    def test_write(self):
        self.hotel_folio.write({'partner_id': self.partner1.id})

    def test_onchange_warehouse_id(self):
        self.hotel_folio.onchange_warehouse_id()

    def test_onchange_partner_id(self):
        self.hotel_folio.onchange_partner_id()

    def test_folio_button_dummy(self):
        self.hotel_folio.button_dummy()

    def test_folio_action_done(self):
        self.hotel_folio.action_done()
        self.assertEqual(self.hotel_folio.state == 'done', True)

    def test_folio_action_invoice_create(self):
        with self.assertRaises(UserError):
            self.hotel_folio.action_invoice_create()

    def test_folio_action_cancel(self):
        self.hotel_folio.action_cancel()

    def test_folio_action_confirm(self):
        self.hotel_folio.action_confirm()
        self.assertEqual(self.hotel_folio.state == 'sale', True)
        self.hotel_folio.order_line._action_procurement_create()
        self.assertFalse(self.hotel_folio.project_id, False)
        invoice_policy = self.hotel_folio.order_line.product_id.invoice_policy
        self.assertEqual(invoice_policy == 'cost', False)
        self.hotel_folio.order_id._create_analytic_account()

    def test_folio_action_cancel_draft(self):
        self.hotel_folio.action_cancel_draft()
        self.assertEqual(self.hotel_folio.state == 'draft', True)

    def test_service_type_name_get(self):
        self.hotel_service_type.name_get()

    def test_service_type_name_search(self):
        h_service_type = self.hotel_service_type.name_search('Fixed')
        self.assertEqual(len(h_service_type), 2,
                         'Incorrect search number result for name_search')

    def test_compute_get_currency(self):
        with self.assertRaises(ValidationError):
            self.currency_exchange._compute_get_currency()

    def test_check_out_curr(self):
        self.currency_exchange.check_out_curr()

    def test_get_folio_no(self):
        self.currency_exchange.get_folio_no()

    def test_act_cur_done(self):
        self.currency_exchange.act_cur_done()
        self.assertEqual(self.currency_exchange.state == 'done', True)

    def test_act_cur_cancel(self):
        self.currency_exchange.act_cur_cancel()
        self.assertEqual(self.currency_exchange.state == 'cancel', True)

    def test_act_cur_cancel_draft(self):
        self.currency_exchange.act_cur_cancel_draft()
        self.assertEqual(self.currency_exchange.state == 'draft', True)
