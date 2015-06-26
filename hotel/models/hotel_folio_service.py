from openerp.osv import fields
import time
from openerp import netsvc, models, fields, api
from mx import DateTime
import datetime
from openerp.tools import config

class HotelFolioService(models.Model):
    _name = 'hotel.folio.service'
    _description = 'Hotel Folio Service'
    _inherits = {'sale.order.line':'service_line_id'}
    
    @api.one
    def copy(self, default=None):
        copy = self.env['sale.order.line'].browse(id)
        return  copy.copy(default=None)
    
    @api.multi
    def _amount_line_net(self, field_name, arg):
        amount_line = self.env['sale.order.line'].browse(self.ids)
        return  amount_line._amount_line_net(field_name, arg)
    
    @api.multi
    def _amount_line(self, field_name, arg):
        amount_line = self.env['sale.order.line'].browse(self.ids)
        return  amount_line._amount_line(field_name, arg)
    
    @api.multi
    def _number_packages(self, field_name, arg):
        packages = self.env['sale.order.line'].browse(self.ids)
        return  packages._number_packages(field_name, arg)
    
    @api.model
    def _get_1st_packaging(self):
        return  self.env['sale.order.line']._get_1st_packaging()

    service_line_id = fields.Many2one('sale.order.line', 'service_line_id', required=True, ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio', 'folio_id', ondelete='cascade', required=True)
    

    @api.model
    def create(self, vals, check=True):
        folio = self.env['hotel.folio'].browse([vals['folio_id']])[0]
        vals.update({'order_id':folio.order_id.id})
        return super(HotelFolioService, self).create(vals)
    
    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        change = self.env['sale.order.line'].browse(self.ids)
        return  change.uos_change(product_uos, product_uos_qty=0, product_id=None)
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom_qty = 1
        self.name = self.product_id.product_tmpl_id.name
        self.product_uom = self.product_id.uom_id
        self.price_unit = self.product_id.list_price
        tax_lines = []
        for tax_data in self.product_id.taxes_id: 
            tax_lines.append((6, 0, tax_data.id))           
        self.tax_id = tax_lines 
    
    '''
    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        line_ids = [folio.order_line_id.id for folio in self]
        if product:
            return self.env['sale.order.line'].browse(line_ids).product_id_change(pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)
        
    @api.multi    
    def product_uom_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        if product:
            return  self.product_id_change(pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)
        
    @api.multi    
    def on_change_checkout(self, checkin_date=time.strftime('%Y-%m-%d %H:%M:%S'), checkout_date=time.strftime('%Y-%m-%d %H:%M:%S')):
        qty = 1
        if checkout_date < checkin_date:
            raise osv.except_osv ('Error !', 'Checkout must be greater or equal checkin date')
        if checkin_date:
            diffDate = datetime.datetime(*time.strptime(checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
            qty = diffDate.days
        return {'value':{'product_uom_qty':qty}}
    '''
    
    
    @api.multi
    def button_confirm(self):
        button = self.env['sale.order.line'].browse(self.ids)
        return  button.button_confirm()
    
    @api.multi
    def button_done(self):
        button = self.env['sale.order.line'].browse(self.ids)
        return  button.button_done()
    
    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        change = self.env['sale.order.line'].browse(self.ids)
        return  change.uos_change(product_uos, product_uos_qty=0, product_id=None)
    
    @api.one
    def copy(self, default=None):
        copy = self.env['sale.order.line'].browse(self.id)
        return copy.copy(default=None)

