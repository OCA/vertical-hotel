import time
from openerp import netsvc
from openerp import models
from openerp import fields
from openerp import api
from mx import DateTime
import datetime
from openerp.tools import config

class HotelFolioService(models.Model):
    _name = 'hotel.folio.service'
    _description = 'Hotel Folio Service'
    
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
    

    service_line_id = fields.Many2one('sale.order.line',
                                      'service_line_id',
                                      required=True,
                                      ondelete='cascade',
                                      delegate=True)
    folio_id = fields.Many2one('hotel.folio',
                               'folio_id',
                               ondelete='cascade',
                               required=True)
    room_id = fields.Many2one('product.product',
                              'associated room')


    @api.model
    def create(self, vals, check=True):
        folio = self.env['hotel.folio'].browse([vals['folio_id']])[0]
        vals.update({'order_id':folio.order_id.id})
        return super(HotelFolioService, self).create(vals)
    
    
    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        change = self.env['sale.order.line'].browse(self.ids)
        return  change.uos_change(product_uos, 
                                  product_uos_qty=0, 
                                  product_id=None)
        
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom_qty = 1
        if self.product_id.description:
            self.name = self.product_id.description
        else: self.name = self.product_id.name
        self.product_uom = self.product_id.uom_id
        self.price_unit = self.product_id.list_price
        '''tax_lines = []
        for tax_data in self.product_id.taxes_id: 
            tax_lines.append((6, 0, tax_data.id))           
        self.tax_id = tax_lines'''
	self.tax_id=self.product_id.taxes_id 
    
    
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
        return  change.uos_change(product_uos, 
                                  product_uos_qty=0, 
                                  product_id=None)
        
    
    @api.one
    def copy(self, default=None):
        copy = self.env['sale.order.line'].browse(self.id)
        return copy.copy(default=None)

