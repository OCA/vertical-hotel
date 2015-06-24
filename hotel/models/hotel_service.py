from openerp.osv import fields
import time
from openerp import netsvc, models, fields, api
from mx import DateTime
import datetime
from openerp.tools import config

class hotel_service_line(models.Model):
    
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

    _name = 'hotel.service.line'
    _description = 'hotel Service line'
    _inherits = {'sale.order.line':'service_line_id'}
    service_line_id = fields.Many2one('sale.order.line', 'service_line_id', required=True, ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio', 'folio_id', ondelete='cascade')
    
    @api.model
    def create(self, vals, check=True):
        if not context:
            context = {}
        if vals.has_key("folio_id"):
            folio = self.env['hotel.folio'].browse([vals['folio_id']])[0]
            vals.update({'order_id':folio.order_id.id})
        roomline = super(models.Model, self).create(vals)
        return roomline
    
    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        change = self.env['sale.order.line'].browse(self.ids)
        return  change.uos_change(product_uos, product_uos_qty=0, product_id=None)
    
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


class hotel_service_type(models.Model):
    _name = "hotel.service.type"
    _inherits = {'product.category':'ser_id'}
    _description = "Service Type" 
    ser_id = fields.Many2one(
        'product.category',
        string='Category',
        required=True,
        select=True,
        ondelete='cascade')
    _defaults = {
        'isservicetype': lambda * a: 1,
    }

class hotel_services(models.Model):
    
    _name = 'hotel.services'
    _description = 'Hotel Services and its charges'
    _inherits = {'product.product':'service_id'}
    service_id = fields.Many2one('product.product', string='Service', required=True, ondelete='cascade')
    _defaults = {
        'isservice': lambda * a: 1,
        }

