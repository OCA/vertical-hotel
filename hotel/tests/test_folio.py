from openerp.tests.common import TransactionCase
from openerp.tools import mute_logger, float_round
from openerp.exceptions import ValidationError
from openerp.exceptions import except_orm


class TestHotelFolio(TransactionCase):
    """Tests for folio (hotel.folio)
    """

    def setUp(self):
        super(TestHotelFolio, self).setUp()
        self.folioObj = self.env['hotel.folio']
        self.saleOrderObj = self.env['sale.order']
        self.saleOrderLineObj = self.env['sale.order.line']
        self.invoiceObj = self.env['account.invoice']
        self.voucherObj = self.env['account.voucher']
        self.roomlineObj = self.env['hotel.folio.room']
        self.servicelineObj = self.env['hotel.folio.service']
        self.ModelDataObj = self.env['ir.model.data']
        self.partnerObj = self.env['res.partner']

        self.room1_id = self.ModelDataObj.xmlid_to_res_id('hotel.hotel_room_5')
        self.room1 = self.env['hotel.room'].browse(self.room1_id)
        self.room2_id = self.ModelDataObj.xmlid_to_res_id('hotel.hotel_room_6')
        self.room2 = self.env['hotel.room'].browse(self.room2_id)

        print '\n'
        print '         ***Creating room and services***'
        print '                 Room 1 id:', self.room1.product_id.id
        print '                 Room 1 name:', self.room1.name


        self.service1_id = self.ModelDataObj.xmlid_to_res_id('hotel.hotel_service_6')
        self.service1 = self.env['hotel.services'].browse(self.service1_id)
        print '                 Service 1 name:', self.service1.name
        print '\n'

        self.admin = self.partnerObj.browse(3)
        self.testUser = self.partnerObj.browse(10)

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_folio_create(self):
        '''Creating Folio'''
        folio1 = self.folioObj.create({
            'partner_id': self.admin.id,
            'partner_invoice_id': self.admin.id,
            'partner_shipping_id': self.admin.id,
            'checkin_date': '2015-07-20 11:04:38',
            'checkout_date': '2015-07-28 11:04:38',
            'duration': 8,
            'name': 'SSS',
            'date_order': '2015-07-20 11:04:54.09324',
            'pricelist_id': 1,
            'order_policy': 'manual',
            'picking_policy': 'direct',
            'warehouse_id': 1
        })
        self.assertTrue(folio1, 'Error: folio not created')

        print '         ***Creating folio***'
        print '                 Folio id:', folio1.id
        print '                 Folio order id:', folio1.order_id.id
        print '                 Folio hotel policy:', folio1.hotel_policy
        print '                 Folio checin date:', folio1.checkin_date
        print '                 Folio checkout date:', folio1.checkout_date
        print '                 Folio duration:', folio1.duration
        print '                 Folio partner id:', folio1.partner_id.id
        print '                 Folio partner invoice id:', folio1.partner_invoice_id.id
        print '                 Folio partner shipping id:', folio1.partner_shipping_id.id
        print '\n'
        print '         ***Creating sale order***'
        print '                 sale order id:', folio1.order_id.id
        print '                 sale order policy:', folio1.order_id.order_policy
        print '                 sale date order:', folio1.order_id.date_order
        print '                 sale state:', folio1.order_id.state
        print '                 sale partner id:', folio1.order_id.partner_id.id
        print '                 sale partner invoice id:', folio1.order_id.partner_invoice_id.id
        print '                 sale partner shipping id:', folio1.order_id.partner_shipping_id.id
        print '                 sale ammount:', folio1.order_id.amount_untaxed
        print '                 sale ammount tax:', folio1.order_id.amount_tax
        print '                 sale ammount total:', folio1.order_id.amount_total
        print '\n'

        with self.assertRaises(ValidationError):
            room_lines = self.roomlineObj.create({
                'folio_id': folio1.id,
                'product_id': self.room1.product_id.id,
                'name': self.room1.name,
                'checkin_date': '2015-07-20 11:04:38',
                'checkout_date': '2015-07-28 11:04:38',
                'product_uom_qty': 8,
                'price_unit': self.room1.list_price,
                'product_uom': self.room1.uom_id.id,
                'delay': 0,
                'state': 'draft',
                'sequence': 10,
                'price_unit': 200.00,
                'product_uom_qty': folio1.duration
            })

        print '         ***Creating room_ids***'
        print '                 room id:', folio1.room_ids.id
        print '                 room folio id:', folio1.room_ids.folio_id.id
        print '                 room sale order line id:', folio1.room_ids.order_line_id.id
        print '                 room checkin date:', folio1.room_ids.checkin_date
        print '                 room checkout date:', folio1.room_ids.checkout_date
        print '\n'
        print '         ***Creating sale_order_line for room_ids***'
        print '                 sale order line id:', folio1.room_ids.order_line_id.id
        print '                 sale order line sequence:', folio1.room_ids.order_line_id.sequence
        print '                 sale order line price unit:', folio1.room_ids.order_line_id.price_unit
        print '                 sale order line product uom qty:', folio1.room_ids.order_line_id.product_uom_qty
        print '                 sale order line invoiced?:', folio1.room_ids.order_line_id.invoiced
        print '                 sale order line name:', folio1.room_ids.order_line_id.name
        print '                 sale order line delay:', folio1.room_ids.order_line_id.delay
        print '                 sale order line state:', folio1.room_ids.order_line_id.state
        print '                 sale order line order id:', folio1.room_ids.order_line_id.order_id.id
        print '                 sale order line product id:', folio1.room_ids.order_line_id.product_id.id
        print '\n'

        service_lines = self.servicelineObj.create({
                    'folio_id': folio1.id,
                    'product_id': self.service1.service_id.id,
                    'name': self.service1.name,
                    'product_uom_qty': 1,
                    'price_unit': self.service1.list_price,
                    'product_uom': self.room1.uom_id.id,
                    'delay': 0,
                    'state': 'draft',
                    'sequence': 10,
                    'price_unit': 100.00,
                    'product_uom_qty': folio1.duration
        })

        print '         ***Creating service_ids***'
        print '                 service id:', folio1.service_ids.id
        print '                 service folio id:', folio1.service_ids.folio_id.id
        print '                 service sale order line id:', folio1.service_ids.service_line_id.id
        print '\n'
        print '         ***Creating sale_order_line for service_ids***'
        print '                 sale order line id:', folio1.service_ids.service_line_id.id
        print '                 sale order line sequence:', folio1.service_ids.service_line_id.sequence
        print '                 sale order line price unit:', folio1.service_ids.service_line_id.price_unit
        print '                 sale order line product uom qty:', folio1.service_ids.service_line_id.product_uom_qty
        print '                 sale order line invoiced?:', folio1.service_ids.service_line_id.invoiced
        print '                 sale order line name:', folio1.service_ids.service_line_id.name
        print '                 sale order line delay:', folio1.service_ids.service_line_id.delay
        print '                 sale order line state:', folio1.service_ids.service_line_id.state
        print '                 sale order line order id:', folio1.service_ids.service_line_id.order_id.id
        print '                 sale order line product id:', folio1.service_ids.service_line_id.product_id.id
        print '\n'
        print '         ***Compute sale order price***'
        print '                 sale ammount:', folio1.order_id.amount_untaxed
        print '                 sale ammount tax:', folio1.order_id.amount_tax
        print '                 sale ammount total:', folio1.order_id.amount_total
        print '\n'

        # ----------------------------------------------------------------------
        # Check folio1 initial state
        # ----------------------------------------------------------------------
        print '         ***Checking folio1 initial state***'
        print '                 folio1 state:', folio1.state
        print '\n'
        self.assertEqual(folio1.state,
                         'draft',
                         'Folio initial state should be draft!')
        # ----------------------------------------------------------------------
        # Confirm folio1 and check state
        # ----------------------------------------------------------------------
        folio1.action_button_confirm()
        print '         ***Confirming folio1***'
        print '                 folio1 state:', folio1.state
        print '\n'
        self.assertEqual(folio1.state,
                         'manual',
                         'Confirmed folios should be in "manual" state!')
        # ----------------------------------------------------------------------
        # Test onchange_partner_id
        # ----------------------------------------------------------------------
        print '         ***Current folio1 partner_id***'
        print '                 Partner name:', folio1.partner_id.name
        print '                 Partner id:', folio1.partner_id.id
        print '                 Partner shipping id:', folio1.partner_shipping_id.id
        print '                 Partner invoice id:', folio1.partner_invoice_id.id
        print '\n'

        folio1.partner_id=self.testUser.id
        folio1.partner_invoice_id=folio1.onchange_partner_id(self.testUser.id)['value']['partner_invoice_id']
        folio1.partner_shipping_id=folio1.onchange_partner_id(self.testUser.id)['value']['partner_shipping_id']

        self.assertEqual(folio1.partner_id.id,
                         self.testUser.id,
                         'onchange_partner_id method failed!')
        self.assertEqual(folio1.partner_invoice_id.id,
                         self.testUser.id,
                         'onchange_partner_id method failed!')
        self.assertEqual(folio1.partner_shipping_id.id,
                         self.testUser.id,
                         'onchange_partner_id method failed!')

        print '         ***Updated folio1 partner_id***'
        print '                 Partner name:', folio1.partner_id.name
        print '                 Partner id:', folio1.partner_id.id
        print '                 Partner shipping id:', folio1.partner_shipping_id.id
        print '                 Partner invoice id:', folio1.partner_invoice_id.id
        print '\n'
        # ----------------------------------------------------------------------
        # Test onchange_product_id
        # ----------------------------------------------------------------------
        print '         ***Current product_id***'
        print '                 Product id:', folio1.room_ids.order_line_id.product_id.id
        print '                 Product name:', folio1.room_ids.order_line_id.name
        print '                 Prodcut price:', folio1.room_ids.order_line_id.price_unit
        print '\n'

        folio1.room_ids.product_i = self.room2.product_id.id
        print folio1.room_ids.onchange_product_id()
        print '\n'

        '''self.assertEqual(folio1.partner_id.id,
                         self.testUser.id,
                         'onchange_partner_id method failed!')
        self.assertEqual(folio1.partner_invoice_id.id,
                         self.testUser.id,
                         'onchange_partner_id method failed!')
        self.assertEqual(folio1.partner_shipping_id.id,
                         self.testUser.id,
                         'onchange_partner_id method failed!')'''

        print '         ***Updated product_id***'
        print '                 Product id:', folio1.room_ids.order_line_id.product_id.id
        print '                 Product name:', folio1.room_ids.order_line_id.name
        print '                 Prodcut price:', folio1.room_ids.order_line_id.price_unit
        print '\n'
