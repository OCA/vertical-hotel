from openerp.tests.common import TransactionCase
from openerp.tools import mute_logger, float_round
from openerp.exceptions import ValidationError


class TestHotelFolio(TransactionCase):
    """Tests for folio (hotel.folio)
    """

    def setUp(self):
        super(TestHotelFolio, self).setUp()
        self.partnerObj = self.env['res.partner']
        self.folioObj = self.env['hotel.folio']
        self.saleOrderObj = self.env['sale.order']
        self.saleOrderLineObj = self.env['sale.order.line']
        self.pricelistObj = self.env['product.pricelist']
        self.invoiceObj = self.env['account.invoice']
        self.voucherObj = self.env['account.voucher']
        self.uom = self.env['product.uom']


    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_folio_w(self):
        '''Workflow Folio'''
        folio1 = self.folioObj.create({
            'partner_id': 1,
            'partner_invoice_id': 1,
            'partner_shipping_id': 1,
            'checkin_date': '2015-07-20 11:04:38',
            'checkout_date': '2015-07-28 11:04:38',
            'duration': 8,
            'date_order': '2015-07-20 11:04:54.09324',
            'pricelist_id': 1,
            'hotel_policy': 'manual'
        })

        sale_order = self.saleOrderObj.create({
            'date_order': '2015-07-19 11:04:38',
            'partner_id': partnerObj.id,
            'pricelist_id': pricelistObj.id,
            'partner_invoice_id': partnerObj
            'product_uom': 1,
            'price_unit': 200.00,
            'product_uom_qty': 4.000,
            'name': 'Test Room',
            'delay': 0,
            'state': 'draft',
            'order_id': folio1.id
        })

        print self.folioObj.search([('order_id', '=', sale_order_line1.id)])
        # print self.saleOrderObj.search([('id', '=', folio1.id)])











        
        @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
        def test_folio_flow(self):
            '''Workflow Folio'''
            folio1 = self.folioObj.create({
                'partner_id': 1,
                'partner_invoice_id': 1,
                'partner_shipping_id': 1,
                'checkin_date': '2015-07-20 11:04:38',
                'checkout_date': '2015-07-28 11:04:38',
                'duration': 8,
                'date_order': '2015-07-20 11:04:54.09324',
                'pricelist_id': 1,
                'room_ids': [(0, 0, {
                    'product_id': 7,
                    'name': 'Test Room',
                    'checkin_date': '2015-07-20 11:04:38',
                    'checkout_date': '2015-07-28 11:04:38',
                    'product_uom_qty': 8,
                    'price_unit': 200.00,
                    'product_uom': self.uom
                })],
                'service_ids': [(0, 0, {
                    'product_id': 0,
                    'name': 'Test Service',
                    'product_uom_qty': 1,
                    'price_unit': 100.00
                })]
            })

            print self.saleOrderLineObj.search([('id', '=', folio1.id)])


            self.saleOrderObj.browse(folio1.id).action_button_confirm()
            '''Check if the order has been confirmed correctly'''
            self.assertEqual(self.saleOrderObj.browse(folio1.id).state,
                             'manual',
                             'Folio is in wrong state (Confirm button)')

            self.saleOrderObj.browse(folio1.id).action_invoice_create()
            '''Check if order has invoice created'''
            self.assertEqual(self.saleOrderObj.browse(folio1.id).state,
                             'progress',
                             'Folio is in wrong state (Invoice create)')

            self.cr.execute('SELECT invoice_id \
                             FROM sale_order_invoice_rel \
                             WHERE order_id = '+str(folio1.id))
            res = self.cr.fetchone()

            self.invoiceObj.browse(res).invoice_validate()
            '''Check if invoice is validated'''
            self.assertEqual(self.invoiceObj.browse(res).state,
                             'open',
                             'Invoice is in wrong state (Invoice validate)')

            self.invoiceObj.browse(res).invoice_pay_customer()
            self.cr.execute("""SELECT voucher_id
                             FROM account_voucher_line as v,
                             account_invoice_line as i
                             WHERE v.voucher_id = i.invoice_id""")
            res2 = self.cr.fetchone()

            self.voucherObj.browse(res2).button_proforma_voucher()
            '''Check if invoice has been paid'''
            self.assertEqual(self.invoiceObj.browse(res2).state,
                             'paid',
                             'Invoice is in wrong state (Pay)')
            print self.saleOrderObj.browse(folio1.id).state
            self.assertEqual(self.saleOrderObj.browse(folio1.id).state,
                             'done',
                             'Folio is in wrong state (Done)')
