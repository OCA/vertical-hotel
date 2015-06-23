# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################
from openerp.osv import fields
import time
from openerp import netsvc, models, fields, api
#import ir
from mx import DateTime
import datetime
from openerp.tools import config


class hotel_floor(models.Model):
    _name = "hotel.floor"
    _description = "Floor"
    name = fields.Char('Floor Name', size=64, required=True, select=True)
    sequence = fields.Integer('Sequence', size=64)

class product_category(models.Model):
    _inherit = "product.category"
    isroomtype = fields.Boolean('Is Room Type')
    isamenitype = fields.Boolean('Is amenities Type')
    isservicetype = fields.Boolean('Is Service Type')

class hotel_room_type(models.Model):
    _name = "hotel.room_type"
    _inherits = {'product.category':'cat_id'}
    _description = "Room Type"
    cat_id = fields.Many2one('product.category', 'category', required=True, select=True, ondelete='cascade')

    _defaults = {
        'isroomtype': lambda * a: 1,
    }

class product_product(models.Model):
    _inherit = "product.product"
    isroom = fields.Boolean('Is Room')
    iscategid = fields.Boolean('Is categ id')
    isservice = fields.Boolean('Is Service id')


class hotel_room_amenities_type(models.Model):
    _name = 'hotel.room_amenities_type'
    _description = 'amenities Type'
    _inherits = {'product.category':'cat_id'}
    cat_id = fields.Many2one('product.category', 'category', required=True, ondelete='cascade')
    _defaults = {
        'isamenitype': lambda * a: 1,
        
    }


class hotel_room_amenities(models.Model):
    _name = 'hotel.room_amenities'
    _description = 'Room amenities'
    _inherits = {'product.product':'room_categ_id'}
    room_categ_id = fields.Many2one('product.product', 'Product Category', required=True, ondelete='cascade')
    rcateg_id = fields.Many2one('hotel.room_amenities_type', 'Amenity Category')
    amenity_rate = fields.Integer('Amenity Rate')

    _defaults = {
        'iscategid': lambda * a: 1,
        }

class hotel_room(models.Model):
  
    _name = 'hotel.room'
    _inherits = {'product.product':'product_id'}
    _description = 'Hotel Room'
    product_id = fields.Many2one('product.product', 'Product_id', required=True, ondelete='cascade')
    floor_id = fields.Many2one('hotel.floor', 'Floor No')
    max_adult = fields.Integer('Max Adult')
    max_child = fields.Integer('Max Child')
    avail_status = fields.Selection([('assigned', 'Assigned'), (' unassigned', 'Unassigned')], 'Room Status')
    room_amenities = fields.Many2many('hotel.room_amenities', 'temp_tab', 'room_amenities', 'rcateg_id', 'Room Amenities')
    _defaults = {
        'isroom': lambda * a: 1,
        'rental': lambda * a: 1,
        }


class hotel_folio(models.Model):
    
    @api.model
    def _incoterm_get(self):
        #return  self.pool.get('sale.order')._incoterm_get(cr, uid, context={})
        return  self.env['sale.order']._incoterm_get()
    
    '''@api.one
    def copy(self):
        return  self.pool.get('sale.order').copy(cr, uid, id, default=None, context={})'''
    @api.one
    def copy(self):
        copy = self.env['sale.order'].browse(id)
        return  copy.copy(self)
    
    
    '''@api.multi
    def _invoiced(self, cursor, user, name, arg):
        return  self.pool.get('sale.order')._invoiced(cursor, user, ids, name, arg, context=None)'''
    
    @api.multi
    def _invoiced(self, cursor, user, name, arg):
        invoiced = self.env['sale.order'].browse(ids)
        return  invoiced._invoiced(cursor, user, name, arg)

    @api.model
    def _invoiced_search(self, cursor, user, obj, name, args):
        #return  self.pool.get('sale.order')._invoiced_search(cursor, user, obj, name, args)
        return  self.env['sale.order']._invoiced_search(cursor, user, obj, name, args)
    
    @api.multi
    def _amount_untaxed(self, field_name, arg):
        sales = self.env['sale.order'].browse(self.ids)
        return sales._amount_untaxed(field_name, arg)
    
    '''@api.multi
    def _amount_untaxed(self, field_name, arg):
       return self.pool.get('sale.order')._amount_untaxed(cr, uid, ids, field_name, arg, context)'''
    
    @api.multi
    def _amount_tax(self, field_name, arg):
        amoun_tax = self.env['sale.order'].browse(ids)
        return amount_tax._amount_tax(field_name, arg)
    
    '''@api.multi
    def _amount_tax(self, field_name, arg, context):
        return self.pool.get('sale.order')._amount_tax(cr, uid, ids, field_name, arg, context)'''
    
    @api.multi
    def _amount_total(self, field_name, arg):
        amount = sel.env['sale.order'].browse(ids)
        return amount._amount_total(field_name, arg)
    
    '''@api.multi
    def _amount_total(self, field_name, arg, context):
        return self.pool.get('sale.order')._amount_total(cr, uid, ids, field_name, arg, context)'''
    
    _name = 'hotel.folio'
    
    _description = 'hotel folio new'
    
    _inherits = {'sale.order':'order_id'}
    
    _rec_name = 'order_id'
    
    order_id = fields.Many2one('sale.order', 'order_id', required=True, ondelete='cascade')
    checkin_date = fields.Datetime('Check In', required=True, readonly=True, states={'draft':[('readonly', False)]})
    checkout_date = fields.Datetime('Check Out', required=True, readonly=True, states={'draft':[('readonly', False)]})
    room_lines = fields.One2many('hotel_folio.line', 'folio_id')
    service_lines = fields.One2many('hotel_service.line', 'folio_id')
    hotel_policy = fields.Selection([('prepaid', 'On Booking'), ('manual', 'On Check In'), ('picking', 'On Checkout')], 'Hotel Policy', required=True)
    duration = fields.Float('Duration')
    #tus
    _defaults = {
                 'hotel_policy':'manual'
                 }
    
    _sql_constraints = [
                        ('check_in_out', 'CHECK (checkin_date<=checkout_date)', 'Check in Date Should be less than the Check Out Date!'),
                       ]
    
    @api.multi
    def _check_room_vacant(self):
        #folio = self.browse(cr, uid, ids[0], context=context)
        folio = self.browse(ids[0])
        rooms = [] 
        for room in folio.room_lines:
            if room.product_id in rooms:
                return False
            rooms.append(room.product_id)
        return True
    
    _constraints = [
            (_check_room_vacant, 'You can not allocate the same room twice!', ['room_lines'])
    ]
    
    @api.multi
    def onchange_dates(self, checkin_date=False, checkout_date=False, duration=False):
        value = {}
        if not duration:
            duration = 0
            if checkin_date and checkout_date:
                chkin_dt = datetime.datetime.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')
                chkout_dt = datetime.datetime.strptime(checkout_date, '%Y-%m-%d %H:%M:%S') 
                dur = chkout_dt - chkin_dt
                duration = dur.days
            value.update({'value':{'duration':duration}})
        else:
            if checkin_date:
                chkin_dt = datetime.datetime.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')
                chkout_dt = chkin_dt + datetime.timedelta(days=duration)
                checkout_date = datetime.datetime.strftime(chkout_dt, '%Y-%m-%d %H:%M:%S')
                value.update({'value':{'checkout_date':checkout_date}})
        return value
    
    @api.model
    def create(self, vals, check=True):
        tmp_room_lines = vals.get('room_lines', [])
        tmp_service_lines = vals.get('service_lines', [])
        vals['order_policy'] = vals.get('hotel_policy', 'manual')
        if not vals.has_key("folio_id"):
            vals.update({'room_lines':[], 'service_lines':[]})
            #folio_id = super(hotel_folio, self).create(cr, uid, vals, context)
            folio_id = super(hotel_folio, self).create(vals)
            for line in tmp_room_lines:
                line[2].update({'folio_id':folio_id})
            for line in tmp_service_lines:
                line[2].update({'folio_id':folio_id})
            vals.update({'room_lines':tmp_room_lines, 'service_lines':tmp_service_lines})
            super(hotel_folio, self).write(cr, uid, [folio_id], vals, context)
        else:
            folio_id = super(hotel_folio, self).create(cr, uid, vals, context)
        return folio_id
    
    @api.multi
    def onchange_shop_id(self, shop_id):
        shop_id = self.env['sale.order'].browse(ids)
        return  shop_id.onchange_shop_id(shop_id)
    
    '''@api.multi
    def onchange_shop_id(self, shop_id):
        return  self.pool.get('sale.order').onchange_shop_id(cr, uid, ids, shop_id)'''
    
    @api.multi
    def onchange_partner_id(self, part):
        partner_id = self.env['sale.order'].browse(ids)
        return  partner_id.onchange_partner_id(part)
    
    '''@api.multi
    def onchange_partner_id(self, part):
        return  self.pool.get('sale.order').onchange_partner_id(cr, uid, ids, part)'''
    
    @api.multi
    def button_dummy(self):
        dummy = self.env['sale.order'].browse(ids)
        return  dummy.button_dummy()
    
    '''@api.multi
    def button_dummy(self):
        return  self.pool.get('sale.order').button_dummy(cr, uid, ids, context={})'''
    
    @api.multi
    def action_invoice_create(self, grouped=False, states=['confirmed', 'done']):
       # i = self.pool.get('sale.order').action_invoice_create(cr, uid, ids, grouped=False, states=['confirmed', 'done'])
        i = self.env['sale.order'].browse(ids)
        i.action_invoice_create(grouped=False, states=['confirmed', 'done'])
        for line in self.browse(cr, uid, ids, context={}):
            self.write(cr, uid, [line.id], {'invoiced':True})
            if grouped:
               self.write(cr, uid, [line.id], {'state' : 'progress'})
            else:
               self.write(cr, uid, [line.id], {'state' : 'progress'})
        return i 

    @api.multi
    def action_invoice_cancel(self):
        #res = self.pool.get('sale.order').action_invoice_cancel(cr, uid, ids, context={})
        res = self.env['sale.order'].browse(ids)
        res.action_invoice_cancel()
        #for sale in self.browse(cr, uid, ids):
        for sale in self.browse(ids):
            for line in sale.order_line:
                #self.pool.get('sale.order.line').write(cr, uid, [line.id], {'invoiced': invoiced})
                self.env['sale.order.line'].write(cr, uid, [line.id], {'invoiced': invoiced})
        self.write(cr, uid, ids, {'state':'invoice_except', 'invoice_id':False})
        return res  
    
    @api.multi
    def action_cancel(self):
        #c = self.pool.get('sale.order').action_cancel(cr, uid, ids, context={})
        c = self.env['sale.order'].browse(ids)
        c.action_cancel()
        ok = True
        #for sale in self.browse(cr, uid, ids):ç
        for sale in self.browse(ids):
            #for r in self.read(cr, uid, ids, ['picking_ids']):
            for r in self.read(['picking_ids']):
                for pick in r['picking_ids']:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'stock.picking', pick, 'button_cancel', cr)
            for r in self.read(cr, uid, ids, ['invoice_ids']):
                for inv in r['invoice_ids']:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'account.invoice', inv, 'invoice_cancel', cr)
            
        #self.write(cr, uid, ids, {'state':'cancel'})
        self.write({'state':'cancel'})
        return c
    
    @api.multi
    def action_wait(self, *args):
        #res = self.pool.get('sale.order').action_wait(cr, uid, ids, *args)
        res = self.env['sale.order']
        res.action_wait(*args)
        #for o in self.browse(cr, uid, ids):
        for o in self.browse(ids):
            if (o.order_policy == 'manual') and (not o.invoice_ids):
                self.write(cr, uid, [o.id], {'state': 'manual'})
            else:
                self.write(cr, uid, [o.id], {'state': 'progress'})
        return res
    
    @api.multi
    def test_state(self, mode, *args):
        write_done_ids = []
        write_cancel_ids = []
        #res = self.pool.get('sale.order').test_state(cr, uid, ids, mode, *args)
        res = self.env['sale.order']
        res.test_state(mode, *args)
        if write_done_ids:
            #self.pool.get('sale.order.line').write(cr, uid, write_done_ids, {'state': 'done'})ç
            self.env['sale.order.line'].write(write_done_ids, {'state': 'done'})
        if write_cancel_ids:
            #self.pool.get('sale.order.line').write(cr, uid, write_cancel_ids, {'state': 'cancel'})
            self.env['sale.order.line'].write(write_cancel_ids, {'state': 'cancel'})
        return res 
    
    @api.multi
    def procurement_lines_get(self, *args):
        #res = self.pool.get('sale.order').procurement_lines_get(cr, uid, ids, *args)
        res = self.env['sale.order'].brose(ids).procurement_lines_get(*args)
        return  res
    
    @api.multi
    def action_ship_create(self, *args):
        #res = self.pool.get('sale.order').action_ship_create(cr, uid, ids, *args)
        res = self.env['sale.order'].browse(ids).action_ship_create(*args)
        return res
    
    @api.multi
    def action_ship_end(self):
        #res = self.pool.get('sale.order').action_ship_end(cr, uid, ids, context={})
        res = self.env['sale.order'].browse(ids).action_ship_end()
        #for order in self.browse(cr, uid, ids):
        for order in self.browse(ids):
            val = {'shipped':True}
            self.write(cr, uid, [order.id], val)
        return res 
    
    @api.multi
    def _log_event(self, factor=0.7, name='Open Order'):
       # return  self.pool.get('sale.order')._log_event(cr, uid, ids, factor=0.7, name='Open Order')
       event = self.env['sale.order'].browse(ids)
       return  event._log_event(factor=0.7, name='Open Order')
    
    @api.multi
    def has_stockable_products(self, *args):
        #return  self.pool.get('sale.order').has_stockable_products(cr, uid, ids, *args)
        products = self.env['sale.order'].browse(ids)
        return products.has_stockable_products(*args)
    
    @api.multi
    def action_cancel_draft(self, *args):
        ''''d = self.pool.get('sale.order').action_cancel_draft(cr, uid, ids, *args)
        self.write(cr, uid, ids, {'state':'draft', 'invoice_ids':[], 'shipped':0})
        self.pool.get('sale.order.line').write(cr, uid, ids, {'invoiced':False, 'state':'draft', 'invoice_lines':[(6, 0, [])]})'''
        d = self.env['sale.order'].browse(ids).action_cancel_draft(*args)
        self.write({'state':'draft', 'invoice_ids':[], 'shipped':0})
        self.env['sale.order.line'].write({'invoiced':False, 'state':'draft', 'invoice_lines':[(6, 0, [])]})
        return d

class hotel_folio_line(models.Model):
    
    @api.one
    def copy(self, default=None):
        #return  self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context={})
        copy = self.env['sale.order.line'].browse(id)
        return  copy.copy(default=None)
    
    @api.multi
    def _amount_line_net(self, field_name, arg):
        #return  self.pool.get('sale.order.line')._amount_line_net(cr, uid, ids, field_name, arg, context)
        amount_line = self.env['sale.order.line'].browse(ids)
        return  amount_line._amount_line_net(field_name, arg)
    
    @api.multi
    def _amount_line(self, field_name, arg):
        #return  self.pool.get('sale.order.line')._amount_line(cr, uid, ids, field_name, arg, context)
        amount_line = self.env['sale.order.line'].browse(ids)
        return  amount_line._amount_line(field_name, arg)
    
    @api.multi
    def _number_packages(self, field_name, arg):
        #return  self.pool.get('sale.order.line')._number_packages(cr, uid, ids, field_name, arg, context)
        packages = self.env['sale.order.line'].browse(ids)
        return  packages._number_packages(field_name, arg)
    
    @api.model
    def _get_1st_packaging(self):
        #return  self.pool.get('sale.order.line')._get_1st_packaging(cr, uid, context={})
        return  self.env['sale.order.line']._get_1st_packaging()
    
    @api.model
    def _get_checkin_date(self):
        if 'checkin_date' in context:
            return context['checkin_date']
        return time.strftime('%Y-%m-%d %H:%M:%S')
    
    @api.model
    def _get_checkout_date(self):
        if 'checkin_date' in context:
            return context['checkout_date']
        return time.strftime('%Y-%m-%d %H:%M:%S')
 
    _name = 'hotel_folio.line'
    _description = 'hotel folio1 room line'
    _inherits = {'sale.order.line':'order_line_id'}
    order_line_id = fields.Many2one('sale.order.line', 'order_line_id', required=True, ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio', 'folio_id', ondelete='cascade')
    checkin_date = fields.Datetime('Check In', required=True)
    checkout_date = fields.Datetime('Check Out', required=True)

    _defaults = {
       'checkin_date':_get_checkin_date,
       'checkout_date':_get_checkout_date,
       
    }
    
    @api.model
    def create(self, vals, check=True):
        if not context:
            context = {}
        if vals.has_key("folio_id"):
            #folio = self.pool.get("hotel.folio").browse(cr, uid, [vals['folio_id']])[0]
            folio = self.env['hotel.folio'].browse([vals['folio_id']])[0]
            vals.update({'order_id':folio.order_id.id})
        #roomline = super(models.Model, self).create(cr, uid, vals, context)
        roomline = super(models.Model, self).create(vals)
        return roomline
    
    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        #return  self.pool.get('sale.order.line').uos_change(cr, uid, ids, product_uos, product_uos_qty=0, product_id=None)
        change = self.env['sale.order.line']
        return  change.uos_change(product_uos, product_uos_qty=0, product_id=None)
    
    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        #return  self.pool.get('sale.order.line').product_id_change(cr, uid, ids, pricelist, product, qty=0,
         #   uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
          #  lang=False, update_tax=True, date_order=False)
          
        return  self.env['sale.order.line'].browse(ids).product_id_change(pricelist, product, qty=0,
        uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
        lang=False, update_tax=True, date_order=False)
    
    @api.multi    
    def product_uom_change(self, cursor, user, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        '''return  self.pool.get('sale.order.line').product_uom_change(cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False) '''
        return  self.env['sale.order.line'].browse(ids).product_uom_change(cursor, user, pricelist, product, qty=0,
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
            if qty == 0:
                qty = 1
        return {'value':{'product_uom_qty':qty}}
    
    @api.multi
    def button_confirm(self):
        #return  self.pool.get('sale.order.line').button_confirm(cr, uid, ids, context={})
        confirm = self.env['sale.order.line'].browse(ids)
        return  confirm.button_confirm()
    
    @api.multi
    def button_done(self):
        #res = self.pool.get('sale.order.line').button_done(cr, uid, ids, context={})
        res = self.env['sale.order.line'].browse(ids).button_done()
        wf_service = netsvc.LocalService("workflow")
        #res = self.write(cr, uid, ids, {'state':'done'})
        res = self.write({'state':'done'})
        #for line in self.browse(cr, uid, ids, context):
        for line in self.browse(ids):
            wf_service.trg_write(uid, 'sale.order', line.order_id.id, cr)
        return res

    @api.multi    
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        #return  self.pool.get('sale.order.line').uos_change(cr, uid, ids, product_uos, product_uos_qty=0, product_id=None)
        change = self.env['sale.order.line'].browse(ids)
        return  change.uos_change(product_uos, product_uos_qty=0, product_id=None)
    
    @api.one
    def copy(self, default=None):
        #return  self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context={})
        copy = self.env['sale.order.line'].browse(id)
        return  copy.copy(default=None)

class hotel_service_line(models.Model):
    
    @api.one
    def copy(self, default=None):
        #return  self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context={})
        copy = self.env['sale.order.line'].browse(id)
        return  copy.copy(default=None)
    
    @api.multi
    def _amount_line_net(self, field_name, arg):
        #return  self.pool.get('sale.order.line')._amount_line_net(cr, uid, ids, field_name, arg, context)
        amount_line = self.env['sale.order.line'].browse(ids)
        return  amount_line._amount_line_net(field_name, arg)
    
    @api.multi
    def _amount_line(self, field_name, arg):
        #return  self.pool.get('sale.order.line')._amount_line(cr, uid, ids, field_name, arg, context)
        amount_line = self.env['sale.order.line'].browse(ids)
        return  amount_line._amount_line(field_name, arg)
    
    @api.multi
    def _number_packages(self, field_name, arg):
        #return  self.pool.get('sale.order.line')._number_packages(cr, uid, ids, field_name, arg, context)
        packages = self.env['sale.order.line'].browse(ids)
        return  packages._number_packages(field_name, arg)
    
    @api.model
    def _get_1st_packaging(self):
        #return  self.pool.get('sale.order.line')._get_1st_packaging(cr, uid, context={})
        return  self.env['sale.order.line']._get_1st_packaging()
   
 
    _name = 'hotel_service.line'
    _description = 'hotel Service line'
    _inherits = {'sale.order.line':'service_line_id'}
    service_line_id = fields.Many2one('sale.order.line', 'service_line_id', required=True, ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio', 'folio_id', ondelete='cascade')
    
    @api.model
    def create(self, vals, check=True):
        if not context:
            context = {}
        if vals.has_key("folio_id"):
            #folio = self.pool.get("hotel.folio").browse(cr, uid, [vals['folio_id']])[0]
            folio = self.env['hotel.folio'].browse([vals['folio_id']])[0]
            vals.update({'order_id':folio.order_id.id})
        #roomline = super(models.Model, self).create(cr, uid, vals, context)
        roomline = super(models.Model, self).create(vals)
        return roomline
    
    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        #return  self.pool.get('sale.order.line').uos_change(cr, uid, ids, product_uos, product_uos_qty=0, product_id=None)
        change = self.env['sale.order.line'].browse(ids)
        return  change.uos_change(product_uos, product_uos_qty=0, product_id=None)
    
    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        '''return  self.pool.get('sale.order.line').product_id_change(cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)'''
        return  self.env['sale.order.line'].browse(ids).product_id_change(pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)
        
    @api.multi    
    def product_uom_change(self, cursor, user, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        '''return  self.pool.get('sale.order.line').product_uom_change(cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)'''
        return  self.env['sale.order.line'].browse(ids).product_uom_change(cursor, user, pricelist, product, qty=0,
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
        #return  self.pool.get('sale.order.line').button_confirm(cr, uid, ids, context={})
        button = self.env['sale.order.line'].browse(ids)
        return  button.button_confirm()
    
    @api.multi
    def button_done(self):
        #return  self.pool.get('sale.order.line').button_done(cr, uid, ids, context={})
        button = self.env['sale.order.line'].browse(ids)
        return  button.button_done()
    
    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        change = self.env['sale.order.line'].browse(ids)
        return  change.uos_change(product_uos, product_uos_qty=0, product_id=None)
        #return  self.pool.get('sale.order.line').uos_change(cr, uid, ids, product_uos, product_uos_qty=0, product_id=None)
    
    @api.one
    def copy(self, default=None):
        #return  self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context={})
        copy = self.env['sale.order.line'].browse(id)
        return copy.copy(default=None)


class hotel_service_type(models.Model):
    _name = "hotel.service_type"
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

