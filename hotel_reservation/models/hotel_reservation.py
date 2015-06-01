# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp import models,fields,api,_
from openerp.exceptions import except_orm, Warning, RedirectWarning
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class hotel_folio(models.Model):
    _inherit = 'hotel.folio'
    _order = 'reservation_id desc'
    
    reservation_id = fields.Many2one(comodel_name='hotel.reservation',string='Reservation Id')

class hotel_reservation(models.Model):
    _name = "hotel.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = 'reservation_no desc'

    reservation_no = fields.Char('Reservation No', size=64,readonly=True, default=lambda obj: obj.env['ir.sequence'].get('hotel.reservation'))
    date_order = fields.Datetime('Date Ordered', required=True, readonly=True, states={'draft':[('readonly', False)]},default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    warehouse_id = fields.Many2one('stock.warehouse','Hotel', readonly=True, required=True, states={'draft':[('readonly', False)]})
    partner_id = fields.Many2one('res.partner','Guest Name' ,readonly=True, required=True, states={'draft':[('readonly', False)]})
    pricelist_id = fields.Many2one('product.pricelist','Price List' ,required=True, readonly=True, states={'draft':[('readonly', False)]}, help="Pricelist for current reservation. ")
    partner_invoice_id = fields.Many2one('res.partner','Invoice Address' ,readonly=True, states={'draft':[('readonly', False)]}, help="Invoice address for current reservation. ")
    partner_order_id = fields.Many2one('res.partner','Ordering Contact',readonly=True, states={'draft':[('readonly', False)]}, help="The name and address of the contact that requested the order or quotation.")
    partner_shipping_id = fields.Many2one('res.partner','Delivery Address' ,readonly=True, states={'draft':[('readonly', False)]}, help="Delivery address for current reservation. ")
    checkin = fields.Datetime('Expected-Date-Arrival', required=True, readonly=True, states={'draft':[('readonly', False)]})
    checkout = fields.Datetime('Expected-Date-Departure', required=True, readonly=True, states={'draft':[('readonly', False)]})
    adults = fields.Integer('Adults', size=64, readonly=True, states={'draft':[('readonly', False)]}, help='List of adults there in guest list. ')
    children = fields.Integer('Children', size=64, readonly=True, states={'draft':[('readonly', False)]}, help='Number of children there in guest list. ')
    reservation_line = fields.One2many('hotel_reservation.line','line_id','Reservation Line',help='Hotel room reservation details. ')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('cancel', 'Cancel'), ('done', 'Done')], 'State', readonly=True,default=lambda *a: 'draft')
    folio_id = fields.Many2many('hotel.folio','hotel_folio_reservation_rel','order_id','invoice_id',string='Folio')
    dummy = fields.Datetime('Dummy')

    
    #Checkin date should be greater than the date ordered.
    @api.onchange('date_order','checkin')
    def on_change_checkin(self):
      checkin_date=time.strftime('%Y-%m-%d %H:%M:%S')  
      if self.date_order and self.checkin:  
        if self.checkin < self.date_order:
                raise except_orm(_('Warning'),_('Checkin date should be greater than the current date.'))

#    @api.onchange('date_order','checkin')
#    def on_change_checkin(self):
#      checkin_date=time.strftime('%Y-%m-%d %H:%M:%S')  
#      if self.date_order and checkin_date:  
#        if checkin_date < self.date_order:
#                raise except_orm(_('Warning'),_('Checkin date should be greater than the current date.')
        

#completed in v8 but in 2ways
#    def on_change_checkin(self, cr, uid, ids, date_order, checkin_date=time.strftime('%Y-%m-%d %H:%M:%S'), context=None):
#        if date_order and checkin_date:
#            if checkin_date < date_order:
#                raise orm.except_orm(_('Warning'), _('Checkin date should be greater than the current date.'))
#        return {'value':{}}

    @api.onchange('checkin','checkout')
    def on_change_checkout(self):
      checkout_date=time.strftime('%Y-%m-%d %H:%M:%S')
      print "checkout_date--------------------",checkout_date
      if not (self.checkout and self.checkin):
            return {'value':{}}
      if self.checkout < self.checkin:
                raise except_orm(_('Warning'),_('Checkout date should be greater than Checkin date.'))       
     # delta = datetime.timedelta(days=1)
    #  addDays = datetime(*time.strptime(self.checkout, '%Y-%m-%d %H:%M:%S')[:5]) + delta
    #  self.dummy = addDays.strftime('%Y-%m-%d %H:%M:%S')
    #  print "self.dummy=-----------------------------",self.delta

#completed in v8 but dummy...!!!!!
#    def on_change_checkout(self, cr, uid, ids, checkin_date=time.strftime('%Y-%m-%d %H:%M:%S'), checkout_date=time.strftime('%Y-%m-%d %H:%M:%S'), context=None):
#        if not (checkout_date and checkin_date):
#            return {'value':{}}
#        if checkout_date < checkin_date:
#            raise orm.except_orm(_('Warning'), _('Checkout date should be greater than the Checkin date.'))
#        delta = datetime.timedelta(days=1)
#        addDays = datetime.datetime(*time.strptime(checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) + delta
#        val = {'value':{'dummy':addDays.strftime('%Y-%m-%d %H:%M:%S')}}
#        return val

    #onchange of partner id pricelist,invoice adress,delivery address,Ordering contact
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.partner_invoice_id = False
            self.partner_shipping_id=False 
            self.partner_order_id=False
        else:
            partner_lst = [self.partner_id.id]
            addr = self.partner_id.address_get(['delivery', 'invoice', 'contact'])
            self.partner_invoice_id = addr['invoice']
            self.partner_order_id = addr['contact'] 
            self.partner_shipping_id = addr['delivery']
            self.pricelist_id=self.env['res.partner'].browse(self.partner_id.id).property_product_pricelist.id

    @api.multi
    def confirmed_reservation(self):
        reservation_line_obj = self.env['hotel.room.reservation.line']
        for reservation in self:
            self._cr.execute("select count(*) from hotel_reservation as hr " \
                        "inner join hotel_reservation_line as hrl on hrl.line_id = hr.id " \
                        "inner join hotel_reservation_line_room_rel as hrlrr on hrlrr.room_id = hrl.id " \
                        "where (checkin,checkout) overlaps ( timestamp %s , timestamp %s ) " \
                        "and hr.id <> cast(%s as integer) " \
                        "and hr.state = 'confirm' " \
                        "and hrlrr.hotel_reservation_line_id in (" \
                        "select hrlrr.hotel_reservation_line_id from hotel_reservation as hr " \
                        "inner join hotel_reservation_line as hrl on hrl.line_id = hr.id " \
                        "inner join hotel_reservation_line_room_rel as hrlrr on hrlrr.room_id = hrl.id " \
                        "where hr.id = cast(%s as integer) )" \
                        , (reservation.checkin, reservation.checkout, str(reservation.id), str(reservation.id)))
            res = self._cr.fetchone()
            roomcount = res and res[0] or 0.0
            if roomcount:
                raise except_orm(_('Warning'), _('You tried to confirm reservation with room those already reserved in this reservation period'))
            else:
                self.write({'state':'confirm'})
                for line_id in reservation.reservation_line:
                    line_id = line_id.reserve
                    for room_id in line_id:
                        vals = {
                            'room_id': room_id.id,
                            'check_in': reservation.checkin,
                            'check_out': reservation.checkout,
                            'state': 'assigned',
                            'reservation_id': reservation.id,
                        }
                        reservation_line_obj.create(vals)
        return True

#completed in v8
#    def confirmed_reservation(self, cr, uid, ids, context=None):
#        reservation_line_obj = self.pool.get('hotel.room.reservation.line')
#        for reservation in self.browse(cr, uid, ids, context=context):
#            cr.execute("select count(*) from hotel_reservation as hr " \
#                        "inner join hotel_reservation_line as hrl on hrl.line_id = hr.id " \
#                        "inner join hotel_reservation_line_room_rel as hrlrr on hrlrr.room_id = hrl.id " \
#                        "where (checkin,checkout) overlaps ( timestamp %s , timestamp %s ) " \
#                        "and hr.id <> cast(%s as integer) " \
#                        "and hr.state = 'confirm' " \
#                        "and hrlrr.hotel_reservation_line_id in (" \
#                        "select hrlrr.hotel_reservation_line_id from hotel_reservation as hr " \
#                        "inner join hotel_reservation_line as hrl on hrl.line_id = hr.id " \
#                        "inner join hotel_reservation_line_room_rel as hrlrr on hrlrr.room_id = hrl.id " \
#                        "where hr.id = cast(%s as integer) )" \
#                        , (reservation.checkin, reservation.checkout, str(reservation.id), str(reservation.id)))
#            res = cr.fetchone()
#            roomcount = res and res[0] or 0.0
#            if roomcount:
#                raise orm.except_orm(_('Warning'), _('You tried to confirm reservation with room those already reserved in this reservation period'))
#            else:
#                self.write(cr, uid, ids, {'state':'confirm'}, context=context)
#                for line_id in reservation.reservation_line:
#                    line_id = line_id.reserve
#                    for room_id in line_id:
#                        vals = {
#                            'room_id': room_id.id,
#                            'check_in': reservation.checkin,
#                            'check_out': reservation.checkout,
#                            'state': 'assigned',
#                            'reservation_id': reservation.id,
#                        }
#                        reservation_line_obj.create(cr, uid, vals, context=context)
#        return True

    @api.multi
    def _create_folio(self):
        hotel_folio_obj = self.env['hotel.folio']
        folio_line_obj = self.env['hotel.folio.line']
        room_obj = self.env['hotel.room']
        for reservation in self:
            folio_lines = []
            checkin_date, checkout_date = self.checkin, self.checkout
            if not self.checkin < self.checkout:
                raise except_orm(_('Error'), _('Invalid values in reservation.\nCheckout date should be greater than the Checkin date.'))
            ch_in = datetime.strptime(self.checkin,DEFAULT_SERVER_DATETIME_FORMAT)
            ch_out = datetime.strptime(self.checkout,DEFAULT_SERVER_DATETIME_FORMAT)
            diff = ch_out - ch_in
            duration = diff.days
            folio_vals = {
                'date_order':reservation.date_order,
                'warehouse_id':reservation.warehouse_id.id,
                'partner_id':reservation.partner_id.id,
                'pricelist_id':reservation.pricelist_id.id,
                'partner_invoice_id':reservation.partner_invoice_id.id,
                'partner_shipping_id':reservation.partner_shipping_id.id,
                'checkin_date': reservation.checkin,
                'checkout_date': reservation.checkout,
                'duration': duration,
                'reservation_id': reservation.id,
                'service_lines':reservation['folio_id']
            }
            folio = hotel_folio_obj.create(folio_vals)
            for line in reservation.reservation_line:
                for r in line.reserve:
                    folio_lines_vals = {
                        'folio_id':folio.id,
                        'order_id':folio.order_id.id,
                        'checkin_date': checkin_date,
                        'checkout_date': checkout_date,
                        'product_id': r.product_id and r.product_id.id,
                        'name': reservation['reservation_no'],
                        'product_uom': r['uom_id'].id,
                        'price_unit': r['lst_price'],
                        'product_uom_qty': (datetime(*time.strptime(reservation['checkout'], '%Y-%m-%d %H:%M:%S')[:5]) - datetime(*time.strptime(reservation['checkin'], '%Y-%m-%d %H:%M:%S')[:5])).days
                    }
                    room_obj.write({'status': 'occupied'})
                    f_id = folio_line_obj.create(folio_lines_vals)
                    
            self._cr.execute('insert into hotel_folio_reservation_rel (order_id, invoice_id) values (%s,%s)', (reservation.id, folio.id))
            reservation.write({'state': 'done'})
        return True

#    def _create_folio(self, cr, uid, ids, context=None):
#        hotel_folio_obj = self.pool.get('hotel.folio')
#        room_obj = self.pool.get('hotel.room')
#        for reservation in self.browse(cr, uid, ids, context=context):
#            folio_lines = []
#            checkin_date, checkout_date = reservation['checkin'], reservation['checkout']
#            if not checkin_date < checkout_date:
#                raise orm.except_orm(_('Error'), _('Invalid values in reservation.\nCheckout date should be greater than the Checkin date.'))
#            duration_vals = hotel_folio_obj.onchange_dates(cr, uid, [], checkin_date=checkin_date, checkout_date=checkout_date, duration=False)
#            duration = duration_vals.get('value', False) and duration_vals['valude'].get('duration') or 0.0
#            folio_vals = {
#                'date_order':reservation.date_order,
#                'warehouse_id':reservation.warehouse_id.id,
#                'partner_id':reservation.partner_id.id,
#                'pricelist_id':reservation.pricelist_id.id,
#                'partner_invoice_id':reservation.partner_invoice_id.id,
#                'partner_shipping_id':reservation.partner_shipping_id.id,
#                'checkin_date': reservation.checkin,
#                'checkout_date': reservation.checkout,
#                'duration': duration,
#                'reservation_id': reservation.id,
#                'service_lines':reservation['folio_id']
#            }
#            for line in reservation.reservation_line:
#                for r in line.reserve:
#                    folio_lines.append((0, 0, {
#                        'checkin_date': checkin_date,
#                        'checkout_date': checkout_date,
#                        'product_id': r.product_id and r.product_id.id,
#                        'name': reservation['reservation_no'],
#                        'product_uom': r['uom_id'].id,
#                        'price_unit': r['lst_price'],
#                        'product_uom_qty': (datetime.datetime(*time.strptime(reservation['checkout'], '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(reservation['checkin'], '%Y-%m-%d %H:%M:%S')[:5])).days
#                    }))
#                    room_obj.write(cr, uid, [r.id], {'status': 'occupied'}, context=context)
#            folio_vals.update({'room_lines': folio_lines})
#            folio = hotel_folio_obj.create(cr, uid, folio_vals, context=context)
#            cr.execute('insert into hotel_folio_reservation_rel (order_id, invoice_id) values (%s,%s)', (reservation.id, folio))
#            self.write(cr, uid, ids, {'state': 'done'}, context=context)
#        return True


class hotel_reservation_line(models.Model):
    _name = "hotel_reservation.line"
    _description = "Reservation Line"

    name = fields.Char('Name', size=64)
    line_id = fields.Many2one('hotel.reservation')
    reserve = fields.Many2many('hotel.room','hotel_reservation_line_room_rel','room_id','hotel_reservation_line_id', domain="[('isroom','=',True),('categ_id','=',categ_id)]")
    categ_id =  fields.Many2one('product.category','Room Type' ,domain="[('isroomtype','=',True)]", change_default=True)

    @api.onchange('categ_id')#,'parent.checkin', 'parent.checkout')
    def on_change_categ(self):
        hotel_room_obj = self.env['hotel.room']
        hotel_room_ids = hotel_room_obj.search([('categ_id', '=',self.categ_id.id)])
        assigned = False
        room_ids = []
        if not self.line_id.checkin:
            raise except_orm(_('Warning'),_('Before choosing a room,\n You have to select a Check in date or a Check out date in the reservation form.'))
        for room in hotel_room_ids:
            assigned = False
            for line in room.room_reservation_line_ids:

                if line.check_in >= self.line_id.checkin and line.check_in <= self.line_id.checkout or line.check_out <= self.line_id.checkout and line.check_out >=self.line_id.checkin:
                    assigned = True

            if not assigned:
                room_ids.append(room.id)
        domain = {'reserve': [('id', 'in', room_ids)]}
        return {'domain': domain}
        
#completed in v8
#    def on_change_categ(self, cr, uid, ids, categ_ids, checkin, checkout, context=None):
#        hotel_room_obj = self.pool.get('hotel.room')
#        hotel_room_ids = hotel_room_obj.search(cr, uid, [('categ_id', '=', categ_ids)], context=context)
#        assigned = False
#        room_ids = []
#        if not checkin:
#            raise orm.except_orm(_('No Checkin date Defined!'), _('Before choosing a room,\n You have to select a Check in date or a Check out date in the reservation form.'))
#        for room in hotel_room_obj.browse(cr, uid, hotel_room_ids, context=context):
#            assigned = False
#            for line in room.room_reservation_line_ids:
#                if line.check_in == checkin and line.check_out == checkout:
#                    assigned = True
#            if not assigned:
#                room_ids.append(room.id)
#        domain = {'reserve': [('id', 'in', room_ids)]}
#        return {'domain': domain}

class hotel_room_reservation_line(models.Model):
    _name = 'hotel.room.reservation.line'
    _description = 'Hotel Room Reservation'
    _rec_name = 'room_id'

    room_id = fields.Many2one(comodel_name='hotel.room',string='Room id')
    check_in = fields.Datetime('Check In Date', required=True)
    check_out = fields.Datetime('Check Out Date', required=True)
    state = fields.Selection([('assigned', 'Assigned'), ('unassigned', 'Unassigned')], 'Room Status')
    reservation_id = fields.Many2one('hotel.reservation',string='Reservation')
     
        
class hotel_room(models.Model):
    _inherit = 'hotel.room'
    _description = 'Hotel Room'

    room_reservation_line_ids = fields.One2many('hotel.room.reservation.line','room_id',string='Room Reservation Line')

    #every 1min scheduler will call this method and check Status of room is occupied or available
    @api.model
    def cron_room_line(self):
        reservation_line_obj = self.env['hotel.room.reservation.line']
        now = datetime.now()
        curr_date = now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        for room in self.search([]):
            reservation_line_ids = [reservation_line.ids for reservation_line in room.room_reservation_line_ids]
            reservation_line_ids = reservation_line_obj.search([('id', 'in', reservation_line_ids),('check_in', '<=', curr_date), ('check_out', '>=', curr_date)])
            if reservation_line_ids:
                room.write({'status':'occupied'})
            else:
              room.write({'status':'available'})
        return True

## vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
