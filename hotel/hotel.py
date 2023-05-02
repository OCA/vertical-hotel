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
from osv import fields, osv
import time
import netsvc
#import ir
from mx import DateTime
import datetime
from tools import config

class hotel_floor(osv.osv):
    _name = "hotel.floor"
    _description = "Floor"
    _columns = { 
        'name': fields.char('Floor Name', size=64, required=True, select=True),
        'sequence' : fields.integer('Sequence', size=64),
        }    
hotel_floor()

class product_category(osv.osv):
    _inherit = "product.category"
    _columns = {
        'isroomtype':fields.boolean('Is Room Type'),
        'isamenitype':fields.boolean('Is amenities Type'),
        'isservicetype':fields.boolean('Is Service Type'),
    }
product_category()

class hotel_room_type(osv.osv):
    _name = "hotel.room_type"
    _inherits = {'product.category':'cat_id'}
    _description = "Room Type"
    _columns = { 
        'cat_id':fields.many2one('product.category', 'category', required=True, select=True, ondelete='cascade'),
   
    }
    _defaults = {
        'isroomtype': lambda * a: 1,
    }    
hotel_room_type()


class product_product(osv.osv):
    _inherit = "product.product"
    _columns = {
        'isroom':fields.boolean('Is Room'),
        'iscategid':fields.boolean('Is categ id'),
        'isservice':fields.boolean('Is Service id'),
                
    }
product_product()

class hotel_room_amenities_type(osv.osv):
    _name = 'hotel.room_amenities_type'
    _description = 'amenities Type'
    _inherits = {'product.category':'cat_id'}
    _columns = {
        'cat_id':fields.many2one('product.category', 'category', required=True, ondelete='cascade'),
       }
    _defaults = {
        'isamenitype': lambda * a: 1,
        
    }

hotel_room_amenities_type()

class hotel_room_amenities(osv.osv):
    _name = 'hotel.room_amenities'
    _description = 'Room amenities'
    _inherits = {'product.product':'room_categ_id'}
    _columns = {
         'room_categ_id':fields.many2one('product.product', 'Product Category', required=True, ondelete='cascade'),
         'rcateg_id':fields.many2one('hotel.room_amenities_type', 'Amenity Catagory'),
         'amenity_rate':fields.integer('Amenity Rate'),
        }
    _defaults = {
        'iscategid': lambda * a: 1,
        }
        
hotel_room_amenities()

class hotel_room(osv.osv):
  
    _name = 'hotel.room'
    _inherits = {'product.product':'product_id'}
    _description = 'Hotel Room'
    _columns = {

        'product_id': fields.many2one('product.product', 'Product_id', required=True, ondelete='cascade'),
        'floor_id':fields.many2one('hotel.floor', 'Floor No'),
        'max_adult':fields.integer('Max Adult'),
        'max_child':fields.integer('Max Child'),
        'avail_status':fields.selection([('assigned', 'Assigned'), (' unassigned', 'Unassigned')], 'Room Status'),
        'room_amenities':fields.many2many('hotel.room_amenities', 'temp_tab', 'room_amenities', 'rcateg_id', 'Room Amenities'),
        }
    _defaults = {
        'isroom': lambda * a: 1,
        'rental': lambda * a: 1,
        }

hotel_room()

class hotel_folio(osv.osv):
    
    def _incoterm_get(self, cr, uid, context={}):
        return  self.pool.get('sale.order')._incoterm_get(cr, uid, context={})
    
    def copy(self, cr, uid, id, default=None, context={}):
        return  self.pool.get('sale.order').copy(cr, uid, id, default=None, context={})
    
    def _invoiced(self, cursor, user, ids, name, arg, context=None):
        return  self.pool.get('sale.order')._invoiced(cursor, user, ids, name, arg, context=None)

    def _invoiced_search(self, cursor, user, obj, name, args):
        return  self.pool.get('sale.order')._invoiced_search(cursor, user, obj, name, args)
    
    def _amount_untaxed(self, cr, uid, ids, field_name, arg, context):
        return self.pool.get('sale.order')._amount_untaxed(cr, uid, ids, field_name, arg, context)
    
    def _amount_tax(self, cr, uid, ids, field_name, arg, context):
        return self.pool.get('sale.order')._amount_tax(cr, uid, ids, field_name, arg, context)
    
    def _amount_total(self, cr, uid, ids, field_name, arg, context):
        return self.pool.get('sale.order')._amount_total(cr, uid, ids, field_name, arg, context)
    
    _name = 'hotel.folio'
    
    _description = 'hotel folio new'
    
    _inherits = {'sale.order':'order_id'}
    
    _rec_name = 'order_id'
    
    _columns = {
          'order_id':fields.many2one('sale.order', 'order_id', required=True, ondelete='cascade'),
          'checkin_date': fields.datetime('Check In', required=True, readonly=True, states={'draft':[('readonly', False)]}),
          'checkout_date': fields.datetime('Check Out', required=True, readonly=True, states={'draft':[('readonly', False)]}),
          'room_lines': fields.one2many('hotel_folio.line', 'folio_id'),
          'service_lines': fields.one2many('hotel_service.line', 'folio_id'),
          'hotel_policy':fields.selection([('prepaid', 'On Booking'), ('manual', 'On Check In'), ('picking', 'On Checkout')], 'Hotel Policy', required=True),
          'duration':fields.float('Duration'),
    }
    
    _defaults = {
                 'hotel_policy':'manual'
                 }
    
    _sql_constraints = [
                        ('check_in_out', 'CHECK (checkin_date<=checkout_date)', 'Check in Date Should be less than the Check Out Date!'),
                       ]
    
    def _check_room_vacant(self, cr, uid, ids, context=None):
        folio = self.browse(cr, uid, ids[0], context=context)
        rooms = [] 
        for room in folio.room_lines:
            if room.product_id in rooms:
                return False
            rooms.append(room.product_id)
        return True
    
    _constraints = [
            (_check_room_vacant, 'You can not allocate the same room twice!', ['room_lines'])
    ]
    
    def onchange_dates(self, cr, uid, ids, checkin_date=False, checkout_date=False, duration=False):
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
    
    def create(self, cr, uid, vals, context=None, check=True):
        tmp_room_lines = vals.get('room_lines', [])
        tmp_service_lines = vals.get('service_lines', [])
        vals['order_policy'] = vals.get('hotel_policy', 'manual')
        if not vals.has_key("folio_id"):
            vals.update({'room_lines':[], 'service_lines':[]})
            folio_id = super(hotel_folio, self).create(cr, uid, vals, context)
            for line in tmp_room_lines:
                line[2].update({'folio_id':folio_id})
            for line in tmp_service_lines:
                line[2].update({'folio_id':folio_id})
            vals.update({'room_lines':tmp_room_lines, 'service_lines':tmp_service_lines})
            super(hotel_folio, self).write(cr, uid, [folio_id], vals, context)
        else:
            folio_id = super(hotel_folio, self).create(cr, uid, vals, context)
        return folio_id
    
   
    def onchange_shop_id(self, cr, uid, ids, shop_id):
        return  self.pool.get('sale.order').onchange_shop_id(cr, uid, ids, shop_id)
    
    def onchange_partner_id(self, cr, uid, ids, part):
        return  self.pool.get('sale.order').onchange_partner_id(cr, uid, ids, part)
    
    def button_dummy(self, cr, uid, ids, context={}):
        return  self.pool.get('sale.order').button_dummy(cr, uid, ids, context={})
    
    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done']):
        i = self.pool.get('sale.order').action_invoice_create(cr, uid, ids, grouped=False, states=['confirmed', 'done'])
        for line in self.browse(cr, uid, ids, context={}):
            self.write(cr, uid, [line.id], {'invoiced':True})
            if grouped:
               self.write(cr, uid, [line.id], {'state' : 'progress'})
            else:
               self.write(cr, uid, [line.id], {'state' : 'progress'})
        return i 

   
    def action_invoice_cancel(self, cr, uid, ids, context={}):
        res = self.pool.get('sale.order').action_invoice_cancel(cr, uid, ids, context={})
        for sale in self.browse(cr, uid, ids):
            for line in sale.order_line:
                self.pool.get('sale.order.line').write(cr, uid, [line.id], {'invoiced': invoiced})
        self.write(cr, uid, ids, {'state':'invoice_except', 'invoice_id':False})
        return res  
    def action_cancel(self, cr, uid, ids, context={}):
        c = self.pool.get('sale.order').action_cancel(cr, uid, ids, context={})
        ok = True
        for sale in self.browse(cr, uid, ids):
            for r in self.read(cr, uid, ids, ['picking_ids']):
                for pick in r['picking_ids']:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'stock.picking', pick, 'button_cancel', cr)
            for r in self.read(cr, uid, ids, ['invoice_ids']):
                for inv in r['invoice_ids']:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'account.invoice', inv, 'invoice_cancel', cr)
            
        self.write(cr, uid, ids, {'state':'cancel'})
        return c
    
    def action_wait(self, cr, uid, ids, *args):
        res = self.pool.get('sale.order').action_wait(cr, uid, ids, *args)
        for o in self.browse(cr, uid, ids):
            if (o.order_policy == 'manual') and (not o.invoice_ids):
                self.write(cr, uid, [o.id], {'state': 'manual'})
            else:
                self.write(cr, uid, [o.id], {'state': 'progress'})
        return res
    def test_state(self, cr, uid, ids, mode, *args):
        write_done_ids = []
        write_cancel_ids = []
        res = self.pool.get('sale.order').test_state(cr, uid, ids, mode, *args)
        if write_done_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_done_ids, {'state': 'done'})
        if write_cancel_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_cancel_ids, {'state': 'cancel'})
        return res 
    def procurement_lines_get(self, cr, uid, ids, *args):
        res = self.pool.get('sale.order').procurement_lines_get(cr, uid, ids, *args)
        return  res
    def action_ship_create(self, cr, uid, ids, *args):
        res = self.pool.get('sale.order').action_ship_create(cr, uid, ids, *args)
        return res
    def action_ship_end(self, cr, uid, ids, context={}):
        res = self.pool.get('sale.order').action_ship_end(cr, uid, ids, context={})
        for order in self.browse(cr, uid, ids):
            val = {'shipped':True}
            self.write(cr, uid, [order.id], val)
        return res 
    def _log_event(self, cr, uid, ids, factor=0.7, name='Open Order'):
        return  self.pool.get('sale.order')._log_event(cr, uid, ids, factor=0.7, name='Open Order')
    def has_stockable_products(self, cr, uid, ids, *args):
        return  self.pool.get('sale.order').has_stockable_products(cr, uid, ids, *args)
    def action_cancel_draft(self, cr, uid, ids, *args):
        d = self.pool.get('sale.order').action_cancel_draft(cr, uid, ids, *args)
        self.write(cr, uid, ids, {'state':'draft', 'invoice_ids':[], 'shipped':0})
        self.pool.get('sale.order.line').write(cr, uid, ids, {'invoiced':False, 'state':'draft', 'invoice_lines':[(6, 0, [])]})
        return d
  
hotel_folio()

class hotel_folio_line(osv.osv):
    
    def copy(self, cr, uid, id, default=None, context={}):
        return  self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context={})
    def _amount_line_net(self, cr, uid, ids, field_name, arg, context):
        return  self.pool.get('sale.order.line')._amount_line_net(cr, uid, ids, field_name, arg, context)
    def _amount_line(self, cr, uid, ids, field_name, arg, context):
        return  self.pool.get('sale.order.line')._amount_line(cr, uid, ids, field_name, arg, context)
    def _number_packages(self, cr, uid, ids, field_name, arg, context):
        return  self.pool.get('sale.order.line')._number_packages(cr, uid, ids, field_name, arg, context)
    def _get_1st_packaging(self, cr, uid, context={}):
        return  self.pool.get('sale.order.line')._get_1st_packaging(cr, uid, context={})
    def _get_checkin_date(self, cr, uid, context={}):
        if 'checkin_date' in context:
            return context['checkin_date']
        return time.strftime('%Y-%m-%d %H:%M:%S')
    def _get_checkout_date(self, cr, uid, context={}):
        if 'checkin_date' in context:
            return context['checkout_date']
        return time.strftime('%Y-%m-%d %H:%M:%S')
 
    _name = 'hotel_folio.line'
    _description = 'hotel folio1 room line'
    _inherits = {'sale.order.line':'order_line_id'}
    _columns = {
          'order_line_id':fields.many2one('sale.order.line', 'order_line_id', required=True, ondelete='cascade'),
          'folio_id':fields.many2one('hotel.folio', 'folio_id', ondelete='cascade'),
          'checkin_date': fields.datetime('Check In', required=True),
          'checkout_date': fields.datetime('Check Out', required=True),
    }
    _defaults = {
       'checkin_date':_get_checkin_date,
       'checkout_date':_get_checkout_date,
       
    }
    
    def create(self, cr, uid, vals, context=None, check=True):
        if not context:
            context = {}
        if vals.has_key("folio_id"):
            folio = self.pool.get("hotel.folio").browse(cr, uid, [vals['folio_id']])[0]
            vals.update({'order_id':folio.order_id.id})
        roomline = super(osv.osv, self).create(cr, uid, vals, context)
        return roomline
    
    def uos_change(self, cr, uid, ids, product_uos, product_uos_qty=0, product_id=None):
        return  self.pool.get('sale.order.line').uos_change(cr, uid, ids, product_uos, product_uos_qty=0, product_id=None)
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        return  self.pool.get('sale.order.line').product_id_change(cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)
        
    def product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        return  self.pool.get('sale.order.line').product_uom_change(cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)
        
    def on_change_checkout(self, cr, uid, ids, checkin_date=time.strftime('%Y-%m-%d %H:%M:%S'), checkout_date=time.strftime('%Y-%m-%d %H:%M:%S'), context=None):
        qty = 1
        if checkout_date < checkin_date:
            raise osv.except_osv ('Error !', 'Checkout must be greater or equal checkin date')
        if checkin_date:
            diffDate = datetime.datetime(*time.strptime(checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
            qty = diffDate.days
            if qty == 0:
                qty = 1
        return {'value':{'product_uom_qty':qty}}
    
    def button_confirm(self, cr, uid, ids, context={}):
       
        return  self.pool.get('sale.order.line').button_confirm(cr, uid, ids, context={})
    def button_done(self, cr, uid, ids, context={}):
        res = self.pool.get('sale.order.line').button_done(cr, uid, ids, context={})
        wf_service = netsvc.LocalService("workflow")
        res = self.write(cr, uid, ids, {'state':'done'})
        for line in self.browse(cr, uid, ids, context):
            wf_service.trg_write(uid, 'sale.order', line.order_id.id, cr)
        return res

        
    def uos_change(self, cr, uid, ids, product_uos, product_uos_qty=0, product_id=None):
        return  self.pool.get('sale.order.line').uos_change(cr, uid, ids, product_uos, product_uos_qty=0, product_id=None)
    def copy(self, cr, uid, id, default=None, context={}):
        return  self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context={})
    
        

hotel_folio_line()

class hotel_service_line(osv.osv):
    
    def copy(self, cr, uid, id, default=None, context={}):
        return  self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context={})
    def _amount_line_net(self, cr, uid, ids, field_name, arg, context):
        return  self.pool.get('sale.order.line')._amount_line_net(cr, uid, ids, field_name, arg, context)
    def _amount_line(self, cr, uid, ids, field_name, arg, context):
        return  self.pool.get('sale.order.line')._amount_line(cr, uid, ids, field_name, arg, context)
    def _number_packages(self, cr, uid, ids, field_name, arg, context):
        return  self.pool.get('sale.order.line')._number_packages(cr, uid, ids, field_name, arg, context)
    def _get_1st_packaging(self, cr, uid, context={}):
        return  self.pool.get('sale.order.line')._get_1st_packaging(cr, uid, context={})
   
 
    _name = 'hotel_service.line'
    _description = 'hotel Service line'
    _inherits = {'sale.order.line':'service_line_id'}
    _columns = {
          'service_line_id':fields.many2one('sale.order.line', 'service_line_id', required=True, ondelete='cascade'),
          'folio_id':fields.many2one('hotel.folio', 'folio_id', ondelete='cascade'),
         
    }

    def create(self, cr, uid, vals, context=None, check=True):
        if not context:
            context = {}
        if vals.has_key("folio_id"):
            folio = self.pool.get("hotel.folio").browse(cr, uid, [vals['folio_id']])[0]
            vals.update({'order_id':folio.order_id.id})
        roomline = super(osv.osv, self).create(cr, uid, vals, context)
        return roomline
    
    def uos_change(self, cr, uid, ids, product_uos, product_uos_qty=0, product_id=None):
        return  self.pool.get('sale.order.line').uos_change(cr, uid, ids, product_uos, product_uos_qty=0, product_id=None)
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        return  self.pool.get('sale.order.line').product_id_change(cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)
    def product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        return  self.pool.get('sale.order.line').product_uom_change(cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)
    def on_change_checkout(self, cr, uid, ids, checkin_date=time.strftime('%Y-%m-%d %H:%M:%S'), checkout_date=time.strftime('%Y-%m-%d %H:%M:%S'), context=None):
        qty = 1
        if checkout_date < checkin_date:
            raise osv.except_osv ('Error !', 'Checkout must be greater or equal checkin date')
        if checkin_date:
            diffDate = datetime.datetime(*time.strptime(checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
            qty = diffDate.days
        return {'value':{'product_uom_qty':qty}}
    
    def button_confirm(self, cr, uid, ids, context={}):
       
        return  self.pool.get('sale.order.line').button_confirm(cr, uid, ids, context={})
    def button_done(self, cr, uid, ids, context={}):
        return  self.pool.get('sale.order.line').button_done(cr, uid, ids, context={})
    def uos_change(self, cr, uid, ids, product_uos, product_uos_qty=0, product_id=None):
        return  self.pool.get('sale.order.line').uos_change(cr, uid, ids, product_uos, product_uos_qty=0, product_id=None)
    def copy(self, cr, uid, id, default=None, context={}):
        return  self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context={})
    
        

hotel_service_line()

class hotel_service_type(osv.osv):
    _name = "hotel.service_type"
    _inherits = {'product.category':'ser_id'}
    _description = "Service Type"
    _columns = { 
        'ser_id':fields.many2one('product.category', 'category', required=True, select=True, ondelete='cascade'),
        
    }
    _defaults = {
        'isservicetype': lambda * a: 1,
    }    
hotel_service_type()

class hotel_services(osv.osv):
    
    _name = 'hotel.services'
    _description = 'Hotel Services and its charges'
    _inherits = {'product.product':'service_id'}
    _columns = {
        'service_id': fields.many2one('product.product', 'Service_id', required=True, ondelete='cascade'),
       
        }
    _defaults = {
        'isservice': lambda * a: 1,
        }
hotel_services()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
