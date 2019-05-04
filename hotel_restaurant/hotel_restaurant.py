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

from osv import fields
from osv import osv
import time
from mx import DateTime
import netsvc
import datetime
import pooler
from tools import config


class product_category(osv.osv):
    _inherit = "product.category"
    _columns = {
        'ismenutype':fields.boolean('Is Menu Type'),
    }
product_category()
class product_product(osv.osv):
    _inherit = "product.product"
    _columns = {
        'ismenucard':fields.boolean('Is Room'),
        }
product_product()

class hotel_menucard_type(osv.osv):
    _name = 'hotel.menucard.type'
    _description = 'amenities Type'
    _inherits = {'product.category':'menu_id'}
    _columns = {
        'menu_id':fields.many2one('product.category', 'category', required=True, ondelete='cascade'),
       }
    _defaults = {
        'ismenutype': lambda * a: 1,

    }
hotel_menucard_type()

class hotel_menucard(osv.osv):

    _name = 'hotel.menucard'
    _inherits = {'product.product':'product_id'}

    _description = 'Hotel Menucard'
    _columns = {

        'product_id': fields.many2one('product.product', 'Product_id'),
       }
    _defaults = {
        'ismenucard': lambda * a: 1,
        }
hotel_menucard()


class hotel_restaurant_tables(osv.osv):

    _name = "hotel.restaurant.tables"
    _description = "Includes Hotel Restaurant Table"
    _columns = {
        'name':fields.char('Table number', size=64, required=True),
        'capacity':fields.integer('Capacity'),

        }
hotel_restaurant_tables()

class hotel_restaurant_reservation(osv.osv):

    def create_order(self, cr, uid, ids, context=None):
         k = []
         for i in self.browse(cr, uid, ids):
             table_ids = [x.id for x in i.tableno]
             kot_data = self.pool.get('hotel.reservation.order').create(cr, uid, {
                                                                            'reservationno':i.reservation_id,
                                                                            'date1':i.start_date,
                                                                            'table_no':[(6, 0, table_ids)],
                                                                             })


         return True

    def onchange_partner_id(self, cr, uid, ids, part):
         if not part:
             return {'value':{'partner_address_id': False}}
         addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['default'])
         pricelist = self.pool.get('res.partner').browse(cr, uid, part).property_product_pricelist_purchase.id
         return {'value':{'partner_address_id': addr['default']}}

    def action_set_to_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService('workflow')
        for id in ids:
            wf_service.trg_create(uid, self._name, id, cr)
        return True

    def table_reserved(self, cr, uid, ids, *args):

        for reservation in self.browse(cr, uid, ids):

            cr.execute("select count(*) from hotel_restaurant_reservation as hrr " \
                       "inner join reservation_table as rt on rt.reservation_table_id = hrr.id " \
                       "where (start_date,end_date)overlaps( timestamp %s , timestamp %s ) " \
                       "and hrr.id<> %s " \
                       "and rt.name in (select rt.name from hotel_restaurant_reservation as hrr " \
                       "inner join reservation_table as rt on rt.reservation_table_id = hrr.id " \
                       "where hrr.id= %s) " \
                        , (reservation.start_date, reservation.end_date, reservation.id, reservation.id))

            res = cr.fetchone()

            roomcount = res and res[0] or 0.0
            if roomcount:
                raise osv.except_osv('Warning', 'You tried to confirm reservation with table those already reserved in this reservation period')
            else:
                self.write(cr, uid, ids, {'state':'confirm'})
            return True



    def table_cancel(self, cr, uid, ids, *args):

        self.write(cr, uid, ids, {
            'state':'cancel'
        })
        return True

    def table_done(self, cr, uid, ids, *args):

        self.write(cr, uid, ids, {
            'state':'done'
        })
        return True

    _name = "hotel.restaurant.reservation"
    _description = "Includes Hotel Restaurant Reservation"
    _columns = {
        'reservation_id':fields.char('Reservation No', size=64, required=True),
        'room_no':fields.many2one('hotel.room', 'Room No', size=64),
        'start_date':fields.datetime('Start Date', required=True),
        'end_date':fields.datetime('End Date', required=True),
        'cname':fields.many2one('res.partner', 'Customer Name', size=64, required=True),
        'partner_address_id':fields.many2one('res.partner.address', 'Address'),
        'tableno':fields.many2many('hotel.restaurant.tables', 'reservation_table', 'reservation_table_id', 'name', 'Table number'),
        'state' : fields.selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')], 'state', select=True, required=True, readonly=True),
        }
    _defaults = {
        'state': lambda * a: 'draft',
        'reservation_id':lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'hotel.restaurant.reservation'),
    }
    _sql_constraints = [
                        ('check_dates', 'CHECK (start_date<=end_date)', 'Start Date Should be less than the End Date!'),
                       ]
    

hotel_restaurant_reservation()

class hotel_restaurant_kitchen_order_tickets(osv.osv):
    _name = "hotel.restaurant.kitchen.order.tickets"
    _description = "Includes Hotel Restaurant Order"
    _columns = {
        'orderno':fields.char('Order Number', size=64, readonly=True),
        'resno':fields.char('Reservation Number', size=64),
        'kot_date':fields.datetime('Date'),
        'room_no':fields.char('Room No', size=64, readonly=True),
        'w_name':fields.char('Waiter Name', size=64, readonly=True),
        'tableno':fields.many2many('hotel.restaurant.tables', 'temp_table3', 'table_no', 'name', 'Table number', size=64),
        'kot_list':fields.one2many('hotel.restaurant.order.list', 'kot_order_list', 'Order List'),

        }

hotel_restaurant_kitchen_order_tickets()

class hotel_restaurant_order(osv.osv):

    def _sub_total(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for sale in self.browse(cr, uid, ids):
            res[sale.id] = 0.00
            for line in sale.order_list:
                res[sale.id] += line.price_subtotal
        return res


    def _total(self, cr, uid, ids, field_name, arg, context):
       res = {}
       for line in self.browse(cr, uid, ids):
           res[line.id] = line.amount_subtotal + (line.amount_subtotal * line.tax) / 100
       return res

    def generate_kot(self, cr, uid, ids, part):

        for order in self.browse(cr, uid, ids):
            table_ids = [x.id for x in order.table_no]
            kot_data = self.pool.get('hotel.restaurant.kitchen.order.tickets').create(cr, uid, {
                                                                            'orderno':order.order_no,
                                                                            'kot_date':order.o_date,
                                                                            'room_no':order.room_no.name,
                                                                            'w_name':order.waiter_name.name,
                                                                            'tableno':[(6, 0, table_ids)],
                                                                             })

            for order_line in order.order_list:

                o_line = {
                         'kot_order_list':kot_data,
                         'name':order_line.name.id,
                         'item_qty':order_line.item_qty,
                             }
                self.pool.get('hotel.restaurant.order.list').create(cr, uid, o_line)

        return True


    _name = "hotel.restaurant.order"
    _description = "Includes Hotel Restaurant Order"
    _columns = {
        'order_no':fields.char('Order Number', size=64, required=True),
        'o_date':fields.datetime('Date', required=True),
        'room_no':fields.many2one('hotel.room', 'Room No', size=64),
        'waiter_name':fields.many2one('res.partner', 'Waiter Name', size=64, required=True),
        'table_no':fields.many2many('hotel.restaurant.tables', 'temp_table2', 'table_no', 'name', 'Table number', size=64),
        'order_list':fields.one2many('hotel.restaurant.order.list', 'o_list', 'Order List'),
        'tax': fields.float('Tax (%) ', size=64),
        'amount_subtotal': fields.function(_sub_total, method=True, string='Subtotal'),
        'amount_total':fields.function(_total, method=True, string='Total'),



        }
    _defaults = {
     'order_no': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'hotel.restaurant.order'),

     }

hotel_restaurant_order()

class hotel_reservation_order(osv.osv):

    def _sub_total(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for sale in self.browse(cr, uid, ids):
            res[sale.id] = 0.00
            for line in sale.order_list:
                res[sale.id] += line.price_subtotal
        return res


    def _total(self, cr, uid, ids, field_name, arg, context):
       res = {}
       for line in self.browse(cr, uid, ids):
           res[line.id] = line.amount_subtotal + (line.amount_subtotal * line.tax) / 100
       return res

    def reservation_generate_kot(self, cr, uid, ids, part):

        for order in self.browse(cr, uid, ids):
            table_ids = [x.id for x in order.table_no]
            kot_data = self.pool.get('hotel.restaurant.kitchen.order.tickets').create(cr, uid, {
                                                                            'orderno':order.order_number,
                                                                            'resno':order.reservationno,
                                                                            'kot_date':order.date1,
                                                                            'w_name':order.waitername.name,
                                                                            'tableno':[(6, 0, table_ids)],
                                                                             })

            for order_line in order.order_list:

                o_line = {
                         'kot_order_list':kot_data,
                         'name':order_line.name.id,
                         'item_qty':order_line.item_qty,
                             }
                self.pool.get('hotel.restaurant.order.list').create(cr, uid, o_line)

        return True

    _name = "hotel.reservation.order"
    _description = "Reservation Order"
    _columns = {
       'order_number':fields.char('Order No', size=64),
       'reservationno':fields.char('Reservation No', size=64),
       'date1':fields.datetime('Date', required=True),
       'waitername':fields.many2one('res.partner', 'Waiter Name', size=64),
       'table_no':fields.many2many('hotel.restaurant.tables', 'temp_table4', 'table_no', 'name', 'Table number', size=64),
       'order_list':fields.one2many('hotel.restaurant.order.list', 'o_l', 'Order List'),
       'tax': fields.float('Tax (%) ', size=64),
       'amount_subtotal': fields.function(_sub_total, method=True, string='Subtotal'),
       'amount_total':fields.function(_total, method=True, string='Total'),


        }

    _defaults = {
        'order_number':lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'hotel.reservation.order'),
        }

hotel_reservation_order()

class hotel_restaurant_order_list(osv.osv):

    def _sub_total(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for line in self.browse(cr, uid, ids):
           res[line.id] = line.item_rate * int(line.item_qty)
        return res


    def on_change_item_name(self, cr, uid, ids, name, context=None):
      if not name:
         return {'value':{}}
      temp = self.pool.get('hotel.menucard').browse(cr, uid, name, context)
      return {'value':{'item_rate':temp.list_price}}


    _name = "hotel.restaurant.order.list"
    _description = "Includes Hotel Restaurant Order"
    _columns = {
        'o_list':fields.many2one('hotel.restaurant.order'),
        'o_l':fields.many2one('hotel.reservation.order'),
        'kot_order_list':fields.many2one('hotel.restaurant.kitchen.order.tickets'),
        'name':fields.many2one('hotel.menucard', 'Item Name', required=True),
        'item_qty':fields.char('Qty', size=64, required=True),
        'item_rate':fields.float('Rate', size=64),
        'price_subtotal': fields.function(_sub_total, method=True, string='Subtotal'),
         }
hotel_restaurant_order_list()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
