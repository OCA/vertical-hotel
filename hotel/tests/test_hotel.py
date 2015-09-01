from openerp.tests.common import TransactionCase
from openerp.tools import mute_logger
from openerp.exceptions import ValidationError


class TestHotel(TransactionCase):
    """Tests hotel management addon"""

    def setUp(self):
        super(TestHotel, self).setUp()
        self.folioObj = self.env['hotel.folio']
        self.saleOrderObj = self.env['sale.order']
        self.saleOrderLineObj = self.env['sale.order.line']
        self.invoiceObj = self.env['account.invoice']
        self.voucherObj = self.env['account.voucher']
        self.roomlineObj = self.env['hotel.folio.room']
        self.servicelineObj = self.env['hotel.folio.service']
        self.ModelDataObj = self.env['ir.model.data']
        self.partnerObj = self.env['res.partner']

        # ----------------------------------------------------------------------
        # Getting data for two users
        # ----------------------------------------------------------------------
        self.admin = self.partnerObj.browse(3)
        self.testUser = self.partnerObj.browse(1)

        # ----------------------------------------------------------------------
        # Getting data for two rooms
        # ----------------------------------------------------------------------
        self.room1_id = self.ModelDataObj.xmlid_to_res_id('hotel.hotel_room_5')
        self.room1 = self.env['hotel.room'].browse(self.room1_id)
        self.room2_id = self.ModelDataObj.xmlid_to_res_id('hotel.hotel_room_2')
        self.room2 = self.env['hotel.room'].browse(self.room2_id)

        # ----------------------------------------------------------------------
        # Getting servie data
        # ----------------------------------------------------------------------
        self.service1_id = self.ModelDataObj.xmlid_to_res_id(
            'hotel.hotel_service_6'
        )
        self.service1 = self.env['hotel.services'].browse(self.service1_id)

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_folio_create(self):
        '''Creates a new folio'''
        # ----------------------------------------------------------------------
        # Creating a new folio
        # ----------------------------------------------------------------------
        folio0 = self.folioObj.create({
            'partner_id': self.admin.id,
            'partner_invoice_id': self.admin.id,
            'partner_shipping_id': self.admin.id,
            'checkin_date': '2015-07-20 11:04:38',
            'checkout_date': '2015-07-28 11:04:38',
            'duration': 8,
            'name': 'SSS0',
            'date_order': '2015-07-20 11:04:54.09324',
            'pricelist_id': 1,
            'order_policy': 'manual',
            'picking_policy': 'direct',
            'warehouse_id': 1
        })
        # check if folio has been created
        self.assertTrue(folio0, 'Error: folio not created')

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_room_check_dates(self):
        '''Try to book same room twice in overlapping duration
           _check_room_dates()'''
        # ----------------------------------------------------------------------
        # Creating first folio
        # ----------------------------------------------------------------------
        folio1 = self.folioObj.create({
            'partner_id': self.admin.id,
            'partner_invoice_id': self.admin.id,
            'partner_shipping_id': self.admin.id,
            'checkin_date': '2016-07-20 11:04:38',
            'checkout_date': '2016-07-28 11:04:38',
            'duration': 8,
            'name': 'SSS1',
            'date_order': '2015-07-20 11:04:54.09324',
            'pricelist_id': 1,
            'order_policy': 'manual',
            'picking_policy': 'direct',
            'warehouse_id': 1
        })

        self.assertTrue(folio1, 'Error: folio not created')

        # ----------------------------------------------------------------------
        # Booking a room for the folio previously created
        # ----------------------------------------------------------------------
        room_lines1 = self.roomlineObj.create({
            'folio_id': folio1.id,
            'product_id': self.room1.product_id.id,
            'name': self.room1.name,
            'checkin_date': '2016-07-20 11:04:38',
            'checkout_date': '2016-07-28 11:04:38',
            'price_unit': self.room1.list_price,
            'product_uom': self.room1.uom_id.id,
            'delay': 0,
            'state': 'draft',
            'sequence': 10,
            'product_uom_qty': folio1.duration
        })

        self.assertEqual(folio1.order_id,
                         room_lines1.order_line_id.order_id,
                         'Fail to book room for the previously created folio')
        # ----------------------------------------------------------------------
        # Creating second folio
        # ----------------------------------------------------------------------
        folio2 = self.folioObj.create({
            'partner_id': self.testUser.id,
            'partner_invoice_id': self.testUser.id,
            'partner_shipping_id': self.testUser.id,
            'checkin_date': '2016-07-20 11:04:38',
            'checkout_date': '2016-07-28 11:04:38',
            'duration': 8,
            'name': 'SSS2',
            'date_order': '2015-07-20 11:04:54.09324',
            'pricelist_id': 1,
            'order_policy': 'manual',
            'picking_policy': 'direct',
            'warehouse_id': 1
        })

        # ----------------------------------------------------------------------
        # test _check_room_dates()
        # ----------------------------------------------------------------------
        with self.assertRaises(ValidationError):
            room_lines2 = self.roomlineObj.create({
                'folio_id': folio2.id,
                'product_id': self.room1.product_id.id,
                'name': self.room1.name,
                'checkin_date': '2016-07-20 11:04:38',
                'checkout_date': '2016-07-28 11:04:38',
                'price_unit': self.room1.list_price,
                'product_uom': self.room1.uom_id.id,
                'delay': 0,
                'state': 'draft',
                'sequence': 10,
                'product_uom_qty': folio1.duration
            })

        self.assertEqual(folio2.order_id,
                         room_lines2.order_line_id.order_id,
                         'Fail to book room for the previously created folio')

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_state_onchange(self):
        '''Test the states and onchange methods'''
        '''Try to book same room twice in overlapping duration'''
        # ----------------------------------------------------------------------
        # Creating folio
        # ----------------------------------------------------------------------
        folio1 = self.folioObj.create({
            'partner_id': self.admin.id,
            'partner_invoice_id': self.admin.id,
            'partner_shipping_id': self.admin.id,
            'checkin_date': '2016-07-20 11:04:38',
            'checkout_date': '2016-07-28 11:04:38',
            'duration': 8,
            'name': 'SSS1',
            'date_order': '2015-07-20 11:04:54.09324',
            'pricelist_id': 1,
            'order_policy': 'manual',
            'picking_policy': 'direct',
            'warehouse_id': 1
        })
        self.assertTrue(folio1, 'Error: folio not created')

        # ----------------------------------------------------------------------
        # Booking a room for the folio previously created
        # ----------------------------------------------------------------------
        room_lines1 = self.roomlineObj.create({
            'folio_id': folio1.id,
            'product_id': self.room1.product_id.id,
            'name': self.room1.name,
            'checkin_date': '2016-07-20 11:04:38',
            'checkout_date': '2016-07-28 11:04:38',
            'price_unit': self.room1.list_price,
            'product_uom': self.room1.uom_id.id,
            'delay': 0,
            'state': 'draft',
            'sequence': 10,
            'product_uom_qty': folio1.duration
        })
        self.assertEqual(folio1.order_id,
                         room_lines1.order_line_id.order_id,
                         'Fail to book room for the previously created folio')

        # ----------------------------------------------------------------------
        # Test onchange_partner_id()
        # ----------------------------------------------------------------------
        folio1.partner_id = self.testUser.id
        folio1.partner_invoice_id = folio1.onchange_partner_id(
            self.testUser.id)['value']['partner_invoice_id']
        folio1.partner_shipping_id = folio1.onchange_partner_id(
            self.testUser.id)['value']['partner_shipping_id']
        self.assertEqual(folio1.partner_id.id,
                         self.testUser.id,
                         'onchange_partner_id method failed!')
        self.assertEqual(folio1.partner_invoice_id.id,
                         self.testUser.id,
                         'onchange_partner_id method failed!')
        self.assertEqual(folio1.partner_shipping_id.id,
                         self.testUser.id,
                         'onchange_partner_id method failed!')

        # ----------------------------------------------------------------------
        # Test _onchange_dates() and _date_dif
        # ----------------------------------------------------------------------
        # change checking date such that duration is now one day less
        folio1.room_ids.checkin_date = '2016-07-21 11:04:38'
        folio1.room_ids._onchange_dates()
        self.assertEqual(folio1.room_ids.product_uom_qty,
                         7,
                         'Duration not update correctly!')

        # ----------------------------------------------------------------------
        # Test onchange_product_id
        # ----------------------------------------------------------------------
        folio1.room_ids.product_id = self.room2.product_id
        folio1.room_ids.onchange_product_id()
        self.assertEqual(folio1.room_ids.product_id.id,
                         self.room2.product_id.id)
        self.assertEqual(folio1.room_ids.order_line_id.price_unit,
                         self.room2.product_tmpl_id.list_price)
        self.assertEqual(folio1.room_ids.product_id.name,
                         self.room2.product_id.name)

        # ----------------------------------------------------------------------
        # Check folio1 initial state
        # ----------------------------------------------------------------------
        self.assertEqual(folio1.state,
                         'draft',
                         'Folio initial state should be draft!')

        # ----------------------------------------------------------------------
        # Confirm folio1 and check state
        # ----------------------------------------------------------------------
        folio1.action_button_confirm()
        self.assertEqual(folio1.state,
                         'manual',
                         'Confirmed folios should be in "manual" state!')

        # ----------------------------------------------------------------------
        # checking if service is created and booked correctly
        # ----------------------------------------------------------------------
        service_lines1 = self.servicelineObj.create({
            'folio_id': folio1.id,
            'product_id': self.service1.service_id.id,
            'name': self.service1.name,
            'checkin_date': '2016-07-20 11:04:38',
            'checkout_date': '2016-07-28 11:04:38',
            'price_unit': self.service1.list_price,
            'product_uom': self.service1.uom_id.id,
            'delay': 0,
            'state': 'draft',
            'sequence': 10,
            'product_uom_qty': folio1.duration
        })
        self.assertEqual(folio1.order_id,
                         service_lines1.service_line_id.order_id,
                         'Fail to book room for the previously created folio')
