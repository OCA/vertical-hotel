# -*- coding: utf-8 -*-
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
import openerp.addons.decimal_precision as dp
from openerp.exceptions import except_orm, Warning, RedirectWarning
import time
from openerp import netsvc
import datetime

class hotel_floor(models.Model):
    _name = "hotel.floor"
    _description = "Floor"
    
    name = fields.Char('Floor Name', size=64, required=True, select=True)
    sequence = fields.Integer('Sequence', size=64)

class product_category(models.Model):
    _inherit = "product.category"

    isroomtype = fields.Boolean('Is Room Type')
    isamenitytype = fields.Boolean('Is Amenities Type')
    isservicetype = fields.Boolean('Is Service Type')


class hotel_room_type(models.Model):
    _name = "hotel.room.type"
    _description = "Room Type"
    
    cat_id = fields.Many2one('product.category','category', required=True, delegate=True, select=True, ondelete='cascade')

class product_product(models.Model):
    _inherit = "product.product"

    isroom = fields.Boolean('Is Room')
    iscategid = fields.Boolean('Is categ id')
    isservice = fields.Boolean('Is Service id')

class hotel_room_amenities_type(models.Model):
    _name = 'hotel.room.amenities.type'
    _description = 'amenities Type'
    
    cat_id = fields.Many2one('product.category','category', required=True, delegate=True, ondelete='cascade')


class hotel_room_amenities(models.Model):
    _name = 'hotel.room.amenities'
    _description = 'Room amenities'

    room_categ_id = fields.Many2one('product.product','Product Category' ,required=True, delegate=True, ondelete='cascade')
    rcateg_id = fields.Many2one('hotel.room.amenities.type','Amenity Catagory')


class hotel_room(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'

    product_id = fields.Many2one('product.product','Product_id' ,required=True, delegate=True, ondelete='cascade')
    floor_id = fields.Many2one('hotel.floor','Floor No',help='At which floor the room is located.')
    max_adult = fields.Integer('Max Adult')
    max_child = fields.Integer('Max Child')
    room_amenities = fields.Many2many('hotel.room.amenities','temp_tab','room_amenities','rcateg_id',string='Room Amenities',help='List of room amenities. ')
    status = fields.Selection([('available', 'Available'), ('occupied', 'Occupied')], 'Status',default='available')


#    room_rent_ids = fields.One2many('room.rent', 'rent_id', 'Room Rent')
#Unused>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#    def set_room_status_occupied(self, cr, uid, ids, context=None):
#        return self.write(cr, uid, ids, {'status': 'occupied'}, context=context)
##
#    def set_room_status_available(self, cr, uid, ids, context=None):
#        return self.write(cr, uid, ids, {'status': 'available'}, context=context)

class hotel_folio(models.Model):

    @api.multi
    def copy(self,default=None):
        return self.env['sale.order'].copy(default=default)

    @api.multi 
    def _invoiced(self, name, arg):
        print "_invoiced hotel folio--------------"
        return self.env['sale.order']._invoiced()

    @api.multi
    def _invoiced_search(self,name, args,obj):
        print "_invoiced_search hotel folio--------------"
        return self.env['sale.order']._invoiced_search()


    _name = 'hotel.folio'
    _description = 'hotel folio new'
    _rec_name = 'order_id'
    _order = 'id desc'

    name = fields.Char('Folio Number', size=24,default=lambda obj: obj.env['ir.sequence'].get('hotel.folio'),readonly=True)
    order_id = fields.Many2one('sale.order','Order',  delegate=True, required=True, ondelete='cascade')
    checkin_date = fields.Datetime('Check In', required=True, readonly=True, states={'draft':[('readonly', False)]})
    checkout_date = fields.Datetime('Check Out', required=True, readonly=True, states={'draft':[('readonly', False)]})
    room_lines = fields.One2many('hotel.folio.line','folio_id', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Hotel room reservation detail.")
    service_lines = fields.One2many('hotel.service.line','folio_id', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Hotel services detail provide to customer and it will include in main Invoice.")
    hotel_policy = fields.Selection([('prepaid', 'On Booking'), ('manual', 'On Check In'), ('picking', 'On Checkout')], 'Hotel Policy',default='manual', help="Hotel policy for payment that either the guest has to payment at booking time or check-in check-out time.")
    duration = fields.Float('Duration in Days', readonly=True, help="Number of days which will automatically count from the check-in and check-out date. ")

    @api.constrains('checkin_date')
    def check_dates(self):
        if self.checkin_date >= self.checkout_date:
                raise except_orm(_('Warning'),_('Check in Date Should be less than the Check Out Date!'))


    @api.constrains('room_lines')
    def check_room_lines(self):        
        rooms = []
        for room in self.room_lines:
            if room.product_id in room:
                return False
            self.rooms.append(room.product_id)
        return True

#    _constraints = [
#        (_check_room_vacant, 'You cannot allocate the same room twice!', ['room_lines'])
#    ]

    @api.onchange('checkin_date','checkout_date')
    def onchange_dates(self):
#    This mathod gives the duration between check in checkout if customer will leave only for some
#    hour it would be considers as a whole day. If customer will checkin checkout for more or equal
#    hours , which configured in company as additional hours than it would be consider as full days
        print'onchange_dates >>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
        value = {}
        company_obj = self.env['res.company']
        configured_addition_hours = 0
        company_ids = self.env['res.company'].search([])
        if company_ids:
            configured_addition_hours = company_obj.browse(company_ids[0].id).additional_hours

        if not self.duration:
            duration = 0 
            if self.checkin_date and self.checkout_date:
                chkin_dt = datetime.datetime.strptime(self.checkin_date, '%Y-%m-%d %H:%M:%S')
                chkout_dt = datetime.datetime.strptime(self.checkout_date, '%Y-%m-%d %H:%M:%S')
                dur = chkout_dt - chkin_dt
                duration = dur.days
                if configured_addition_hours > 0:
                    additional_hours = abs((dur.seconds / 60) / 60)
                    if additional_hours >= configured_addition_hours:
                        duration += 1
            self.duration=duration           
            value.update({'value':{'duration':duration}})
        else:
            if self.checkin_date:
                chkin_dt = datetime.datetime.strptime(self.checkin_date, '%Y-%m-%d %H:%M:%S')
                chkout_dt = chkin_dt + datetime.timedelta(days=self.duration)
                checkout_date = datetime.datetime.strftime(chkout_dt, '%Y-%m-%d %H:%M:%S')
                value.update({'value':{'checkout_date':checkout_date}})
                
        return value     


    @api.model
    def create(self, vals,check=True):
        tmp_room_lines = vals.get('room_lines', [])
        vals['order_policy'] = vals.get('hotel_policy', 'manual')
        if not 'service_lines' and 'folio_id' in vals:
                vals.update({'room_lines':[]})
                folio_id = super(hotel_folio, self).create(vals)
                for line in (tmp_room_lines):
                    line[2].update({'folio_id':folio_id})
                vals.update({'room_lines':tmp_room_lines})
                super(hotel_folio, self).write(vals)
        else:
            folio_id = super(hotel_folio, self).create(vals)
        print "create hotel folio---------------------"    
        return folio_id       

#completed in v8
#    def create(self, cr, uid, vals, context=None, check=True):
#        tmp_room_lines = vals.get('room_lines', [])
#        vals['order_policy'] = vals.get('hotel_policy', 'manual')
#        if not 'service_lines' and 'folio_id' in vals:
#                vals.update({'room_lines':[]})
#                folio_id = super(hotel_folio, self).create(cr, uid, vals, context=context)
#                for line in (tmp_room_lines):
#                    line[2].update({'folio_id':folio_id})
#                vals.update({'room_lines':tmp_room_lines})
#                super(hotel_folio, self).write(cr, uid, [folio_id], vals, context=context)
#        else:
#            folio_id = super(hotel_folio, self).create(cr, uid, vals, context=context)
#        return folio_id

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        order_ids = [folio.order_id.id for folio in self]
        print'onchange_warehouse_id--order_ids--------------------',order_ids
        x = self.env['sale.order'].onchange_warehouse_id(order_ids)
        print'onchange_warehouse_id--x--------------------',x
        return x

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = {}
        if self.partner_id:
            partner_rec = self.env['res.partner'].browse(self.partner_id.id)
            order_ids = [folio.order_id.id for folio in self]
            if not order_ids:
                self.partner_invoice_id = partner_rec.id 
                self.pricelist_id = partner_rec.property_product_pricelist.id
                raise Warning('Not Any Order For  %s ' % (partner_rec.name))
            else:
                self.partner_invoice_id = partner_rec.id
                self.pricelist_id = partner_rec.property_product_pricelist.id


    @api.multi   
    def button_dummy(self):
        order_ids = [folio.order_id.id for folio in self]
        print "hotel folio-------------button_dummy",order_ids
        return self.env['sale.order'].button_dummy()


    @api.multi
    def action_invoice_create(self,grouped=False, states=['confirmed', 'done']):
        order_ids = [folio.order_id.id for folio in self]
        invoice_id = self.env['sale.order'].action_invoice_create(order_ids, states=['confirmed', 'done'])
        for line in self:
            values = {
                'invoiced': True,
                'state': 'progress' if grouped else 'progress',
            }
            line.write(values)
        print "action_invoice_create hotel folio-------------------"    
        return invoice_id        


    @api.multi
    def action_invoice_cancel(self):
        order_ids = [folio.order_id.id for folio in self]
        res = self.env['sale.order'].action_invoice_cancel()
        for sale in self:
            for line in sale.order_line:
                line.write({'invoiced': 'invoiced'})
        self.write({'state':'invoice_except'})
        print "hotel folio------------------------action_invoice_cancel"
        return res       

    @api.multi
    def action_cancel(self):
        order_ids = [folio.order_id.id for folio in self]
        rv = self.env['sale.order'].action_cancel()
        wf_service = netsvc.LocalService("workflow")
        print "---------------------",self.picking_ids.ids 
        for sale in self:
            for pick in sale.picking_ids.ids:
               print "---------------------",sale.picking_ids 
               # (uid, res_type, res_id, signal, cr)--res_type=model name,res_id=the model instance id the workflow belongs to,signal=the signal name to be fired
               wf_service.trg_validate('stock.picking', pick.id, 'button_cancel')
            for invoice in sale.invoice_ids:
                wf_service.trg_validate('account.invoice', invoice.id, 'invoice_cancel')
            sale.write({'state':'cancel'})
        print "action_cancel hotel folio-----------------"        
        return rv        

#issue.........!!
#    def action_cancel(self, cr, uid, ids, context=None):
#        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids, context=context)]
#        rv = self.pool.get('sale.order').action_cancel(cr, uid, order_ids, context=context)
#        wf_service = netsvc.LocalService("workflow")
#        for sale in self.browse(cr, uid, ids, context=context):
#            for pick in sale.picking_ids:
#                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
#            for invoice in sale.invoice_ids:
#                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_cancel', cr)
#                sale.write({'state':'cancel'})
#        return rv

    @api.multi
    def action_wait(self):
        sale_order_obj = self.env['sale.order']
        res = False
        for o in self.browse(self._ids):
            res = sale_order_obj.action_wait()
            if (o.order_policy == 'manual') and (not o.invoice_ids):
                self.write({'state': 'manual'})
            else:
                self.write({'state': 'progress'})
        print "action wait hotel folio  ---------------------"        
        return res

#completed in v8........!!
#    def action_wait(self, cr, uid, ids, *args):
#        sale_order_obj = self.pool.get('sale.order')
#        res = False
#        for o in self.browse(cr, uid, ids):
#            res = sale_order_obj.action_wait(cr, uid, [o.order_id.id], *args)
#            if (o.order_policy == 'manual') and (not o.invoice_ids):
#                self.write(cr, uid, [o.id], {'state': 'manual'})
#            else:
#                self.write(cr, uid, [o.id], {'state': 'progress'})
#        return res
##         order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
##         res = self.pool.get('sale.order').action_wait(cr, uid, order_ids, *args)
##         for order in self.browse(cr, uid, ids):
##             state = ('progress', 'manual')[int(order.order_policy == 'manual' and not order.invoice_ids)]
##             order.write({'state': state})
##         return res

    @api.multi
    def test_state(self,mode):
        write_done_ids = []
        write_cancel_ids = []
        print "tesr_state hotel folio------------"
        if write_done_ids:
            self.env['sale.order.line'].write({'state': 'done'})
        if write_cancel_ids:
            self.env['sale.order.line'].write({'state': 'cancel'})

#completed in v8..!!
#    def test_state(self, cr, uid, ids, mode, *args):
#        write_done_ids = []
#        write_cancel_ids = []
#        # res = self.pool.get('sale.order').test_state(cr, uid, ids, mode, *args)
#        if write_done_ids:
#            self.pool.get('sale.order.line').write(cr, uid, write_done_ids, {'state': 'done'})
#        if write_cancel_ids:
#            self.pool.get('sale.order.line').write(cr, uid, write_cancel_ids, {'state': 'cancel'})
#        # return res

#    @api.multi
#    def procurement_lines_get(self):
#        order_ids = [folio.order_id.id for folio in self]
#        return True

# comment in workflow so how to do testin....!!
#    def procurement_lines_get(self, cr, uid, ids, *args):
#        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
#        # return self.pool.get('sale.order').procurement_lines_get(cr, uid, order_ids, *args)
#        return True

    @api.multi
    def action_ship_create(self):
        order_ids = [folio.order_id.id for folio in self]
        print "action_ship_create-----------------hotel folio"
        return self.env['sale.order'].action_ship_create()

#complted in v8..!!(wrkflow)
#    def action_ship_create(self, cr, uid, ids, context=None):
#        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
#        return self.pool.get('sale.order').action_ship_create(cr, uid, order_ids, context=None)

    
    @api.multi
    def action_ship_end(self):
        order_ids = [folio.order_id.id for folio in self]
        for order in self:
            order.write ({'shipped':True})
        # return res

#testig...............workflow 
#    def action_ship_end(self, cr, uid, ids, context=None):
#        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
#        # res = self.pool.get('sale.order').action_ship_end(cr, uid, order_ids, context=context)
#        for order in self.browse(cr, uid, ids, context=context):
#            order.write ({'shipped':True})
#        # return res

# unused method..!! :-( sale_stock.py
#    def has_stockable_products(self, cr, uid, ids, *args):
#        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
#        return self.pool.get('sale.order').has_stockable_products(cr, uid, order_ids, *args)

    @api.multi     
    def action_cancel_draft(self):
        if not len(self._ids):
            return False
        ids1=self._ids
        query = "select id from sale_order_line where order_id IN %s and state=%s"
        self._cr.execute(query, (tuple(ids1), 'cancel'))
        cr = self._cr
        line_ids = map(lambda x: x[0],cr.fetchall())
        self.write({'state': 'draft', 'invoice_ids': [], 'shipped': 0})
        self.env['sale.order.line'].write({'invoiced': False, 'state': 'draft', 'invoice_lines': [(6, 0, [])]})
        wf_service = netsvc.LocalService("workflow")
        for inv_id in self._ids:
            # Deleting the existing instance of workflow for SO
            wf_service.trg_delete(self._uid,'sale.order', inv_id,self._cr)
            wf_service.trg_create(self._uid,'sale.order', inv_id,self._cr)
        for (id, name) in self.name_get():
            message = _("The sales order '%s' has been set in draft state.") % (name,)
            self.log(message)
        print "action_cancel_draft===============================hotel.folio"    
        return True

#testing.......workflow
#    def action_cancel_draft(self, cr, uid, ids, *args):
#        if not len(ids):
#            return False
#        cr.execute('select id from sale_order_line where order_id IN %s and state=%s', (tuple(ids), 'cancel'))
#        line_ids = map(lambda x: x[0], cr.fetchall())
#        self.write(cr, uid, ids, {'state': 'draft', 'invoice_ids': [], 'shipped': 0})
#        self.pool.get('sale.order.line').write(cr, uid, line_ids, {'invoiced': False, 'state': 'draft', 'invoice_lines': [(6, 0, [])]})
#        wf_service = netsvc.LocalService("workflow")
#        for inv_id in ids:
#            # Deleting the existing instance of workflow for SO
#            wf_service.trg_delete(uid, 'sale.order', inv_id, cr)
#            wf_service.trg_create(uid, 'sale.order', inv_id, cr)
#        for (id, name) in self.name_get(cr, uid, ids):
#            message = _("The sales order '%s' has been set in draft state.") % (name,)
#            self.log(cr, uid, id, message)
#        return True


class hotel_folio_line(models.Model):

#    def copy(self, cr, uid, id, default=None, context=None):
#        return self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context=context)

#no option for duplicate(copy)..........!!!
    @api.one
    def copy(self,default=None):
        return self.env['sale.order.line'].copy(default=default)

# unused method..!! :-(sale.py
#    def _amount_line(self, cr, uid, ids, field_name, arg, context):
#        return self.pool.get('sale.order.line')._amount_line(cr, uid, ids, field_name, arg, context)

# unused method..!! :-( sale_stock.py
#    def _number_packages(self, cr, uid, ids, field_name, arg, context):
#        return self.pool.get('sale.order.line')._number_packages(cr, uid, ids, field_name, arg, context)

#    @api.model
#    def _get_checkin_date(self):
#        print "get checkin date"
#        if self.checkin_date in self._context:
#            return self._context['checkin_date']
#        return time.strftime('%Y-%m-%d %H:%M:%S')
#
#    @api.model
#    def _get_checkout_date(self):
#        print "get checkout date"
#        if self.checkin_date in self._context:
#            return self._context['checkout_date']
#        return time.strftime('%Y-%m-%d %H:%M:%S')

    _name = 'hotel.folio.line'
    _description = 'hotel folio1 room line'
    
    order_line_id = fields.Many2one('sale.order.line',string='Order Line' ,required=True, delegate=True, ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio',string='Folio', ondelete='cascade')
    checkin_date = fields.Datetime('Check In', required=True)
    checkout_date = fields.Datetime('Check Out', required=True)

#may be unnecessary......!!!!
#    _defaults = {
#        'checkin_date':_get_checkin_date,
#        'checkout_date':_get_checkout_date,
#    }

    @api.model
    def create(self,vals,check=True):
        print "folio line..create,,,,,,,,,,,,,,,,,"
        if 'folio_id' in vals:
            folio = self.env["hotel.folio"].browse(vals['folio_id'])
            vals.update({'order_id':folio.order_id.id})
        print "create--------------------------------------------hotel.folio line"    
        return super(hotel_folio_line, self).create(vals)

#testing
#    def create(self, cr, uid, vals, context=None, check=True):
#        if 'folio_id' in vals:
#            folio = self.pool.get("hotel.folio").browse(cr, uid, vals['folio_id'], context=context)
#            vals.update({'order_id':folio.order_id.id})
#        return super(osv.Model, self).create(cr, uid, vals, context)

    @api.multi
    def unlink(self):
        sale_line_obj = self.env['sale.order.line']
        for line in self.browse(self._ids):
            if line.order_line_id:
                sale_line_obj.unlink()
        print "unlink-============================================hotel.folio.line"
        return super(hotel_folio_line, self).unlink()

#testing......!!
#    def unlink(self, cr, uid, ids, context=None):
#        sale_line_obj = self.pool.get('sale.order.line')
#        for line in self.browse(cr, uid, ids, context=context):
#            if line.order_line_id:
#                sale_line_obj.unlink(cr, uid, [line.order_line_id.id], context=context)
#        return super(hotel_folio_line, self).unlink(cr, uid, ids, context=None)

    @api.multi   
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        line_ids = [folio.order_line_id.id for folio in self]
        print "uos_change----------------------------hotl.folio.line"
        return  self.env['sale.order.line'].uos_change(line_ids, product_uos, product_uos_qty=0, product_id=None)

#testing......!!
#    def uos_change(self, cr, uid, ids, product_uos, product_uos_qty=0, product_id=None):
#        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
#        return  self.pool.get('sale.order.line').uos_change(cr, uid, line_ids, product_uos, product_uos_qty=0, product_id=None)

    @api.multi     
    def product_id_change(self,pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        line_ids = [folio.order_line_id.id for folio in self.browse(self._ids)]
        print "product_id_change=======================hotel.folio.line"
        if product:
            return self.env['sale.order.line'].product_id_change(line_ids, pricelist, product,
                uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
                lang=False, update_tax=True, date_order=False)

#testing.......!!
#    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
#            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
#            lang=False, update_tax=True, date_order=False):
#        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
#        return self.pool.get('sale.order.line').product_id_change(cr, uid, line_ids, pricelist, product, qty=0,
#            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
#            lang=False, update_tax=True, date_order=False)

    @api.multi
    def product_uom_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        if product:
            return self.product_id_change(pricelist, product, qty=0,
                uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
                lang=False, update_tax=True, date_order=False)

#tstng..!!
#    def product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
#            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
#            lang=False, update_tax=True, date_order=False):
#        return self.product_id_change(cursor, user, ids, pricelist, product, qty=0,
#            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
#            lang=False, update_tax=True, date_order=False)

    @api.onchange('checkin_date','checkout_date')
    def on_change_checkout(self):
        print'on_change_checkout -----------------------',self
        if not self.checkin_date:
            self.checkin_date = time.strftime('%Y-%m-%d %H:%M:%S')
            print'checkin_date -----------------------',self.checkin_date
        if not self.checkout_date:
            self.checkout_date = time.strftime('%Y-%m-%d %H:%M:%S')
            print'checkout_date -----------------------',self.checkout_date
        qty = 1
        if self.checkout_date < self.checkin_date:
            raise except_orm(_('Warning'),_('Checkout must be greater or equal to checkin date'))
        if self.checkin_date:
            diffDate = datetime.datetime(*time.strptime(self.checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(self.checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
            qty = diffDate.days
            if qty == 0:
                qty == 1
        self.product_uom_qty = qty
        return {'value':{'product_uom_qty':qty}}

#issue..............when u change checkin it gives warining 
#completed in v8
#    def on_change_checkout(self, cr, uid, ids, checkin_date=None, checkout_date=None, context=None):
#        if not checkin_date:
#            checkin_date = time.strftime('%Y-%m-%d %H:%M:%S')
#        if not checkout_date:
#            checkout_date = time.strftime('%Y-%m-%d %H:%M:%S')
#        qty = 1
#        if checkout_date < checkin_date:
#            raise orm.except_orm(_('Error !'), _('Checkout must be greater or equal checkin date'))
#        if checkin_date:
#            diffDate = datetime.datetime(*time.strptime(checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
#            qty = diffDate.days
#            if qty == 0:
#                qty = 1
#        return {'value':{'product_uom_qty':qty}}

#    @api.multi
#    def button_confirm(self):
#        line_ids = [folio.order_line_id.id for folio in self]
#        return self.env['sale.order.line'].button_confirm(line_ids)

#unused..............!!
#    def button_confirm(self, cr, uid, ids, context=None):
#        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
#        return self.pool.get('sale.order.line').button_confirm(cr, uid, line_ids, context=context)

#    @api.multi   
#    def button_done(self):
#        line_ids = [folio.order_line_id.id for folio in self]
#        res = self.env['sale.order.line'].button_done(line_ids)
#        wf_service = netsvc.LocalService("workflow")
#        res = self.write({'state':'done'})
#        for line in self:
#            wf_service.trg_write('sale.order', line.order_line_id.order_id.id, cr)
#        return res

#unused..............!!
#    def button_done(self, cr, uid, ids, context=None):
#        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
#        res = self.pool.get('sale.order.line').button_done(cr, uid, line_ids, context=context)
#        wf_service = netsvc.LocalService("workflow")
#        res = self.write(cr, uid, ids, {'state':'done'})
#        for line in self.browse(cr, uid, ids, context):
#            wf_service.trg_write(uid, 'sale.order', line.order_line_id.order_id.id, cr)
#        return res

    @api.one
    def copy_data(self,default=None):
        #line_id = self.order_line_id.id
        return self.env['sale.order.line'].copy_data(default=default)


#testing..!!
#    def copy_data(self, cr, uid, id, default=None, context=None):
#        line_id = self.browse(cr, uid, id).order_line_id.id
#        return self.pool.get('sale.order.line').copy_data(cr, uid, line_id, default=None, context=context)


class hotel_service_line(models.Model):

#    def copy(self, cr, uid, id, default=None, context=None):
#        line_id = self.browse(cr, uid, id).service_line_id.id
#        return self.pool.get('sale.order.line').copy(cr, uid, line_id, default=None, context=context)

    #on create error raise so how to check copy..........!!!!!!!
    @api.one
    def copy(self, default=None):
        line_id = self.service_line_id.id
        return self.env['sale.order.line'].copy(line_id, default=default)

#    def _amount_line(self, cr, uid, ids, field_name, arg, context):
#        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
#        return  self.pool.get('sale.order.line')._amount_line(cr, uid, line_ids, field_name, arg, context)

#    def _number_packages(self, cr, uid, ids, field_name, arg, context):
#        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
#        return self.pool.get('sale.order.line')._number_packages(cr, uid, line_ids, field_name, arg, context)
#
    _name = 'hotel.service.line'
    _description = 'hotel Service line'
    
    service_line_id = fields.Many2one('sale.order.line','Service Line', required=True, delegate=True, ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio','Folio',ondelete='cascade')

    @api.model
    def create(self,vals,check=True):
        if self.folio_id in vals:
            folio = self.env['hotel.folio'].browse(vals['folio_id'])
            vals.update({'order_id':folio.order_id.id})
        return super(hotel_service_line, self).create(vals)

#testing.........!!
#    def create(self, cr, uid, vals, context=None, check=True):
#        if 'folio_id' in vals:
#            folio = self.pool.get("hotel.folio").browse(cr, uid, vals['folio_id'], context=context)
#            vals.update({'order_id':folio.order_id.id})
#        return super(osv.Model, self).create(cr, uid, vals, context=context)

    @api.multi
    def unlink(self):
        sale_line_obj = self.env['sale.order.line']
        for line in self.browse(self._ids):
            if line.service_line_id:
                sale_line_obj.unlink()
        return super(hotel_service_line, self).unlink()

#testing.........!!
#on create error raise so how to check unlink..........!!!!!!!
#    def unlink(self, cr, uid, ids, context=None):
#        sale_line_obj = self.pool.get('sale.order.line')
#        for line in self.browse(cr, uid, ids, context=context):
#            if line.service_line_id:
#                sale_line_obj.unlink(cr, uid, [line.service_line_id.id], context=context)
#            return super(hotel_service_line, self).unlink(cr, uid, ids, context=None)

    @api.multi
    def product_id_change(self,pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        line_ids = [folio.service_line_id.id for folio in self]
        print "product_id_change-------------------service line"
        if product:
            return self.env['sale.order.line'].product_id_change(line_ids, pricelist, product, 
                uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
                lang=False, update_tax=True, date_order=False)  

    @api.multi
    def product_uom_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        print "hello product_uom_change service line------------------"
        if product:
            return self.product_id_change(pricelist, product, qty=0,
                uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
                lang=False, update_tax=True, date_order=False)

    @api.onchange('checkin_date','checkout_date')
    def on_change_checkout(self):
        if not self.checkin_date:
            self.checkin_date = time.strftime('%Y-%m-%d %H:%M:%S')
        if not self.checkout_date:
            self.checkout_date = time.strftime('%Y-%m-%d %H:%M:%S')
        qty = 1
        if self.checkout_date < self.checkin_date:
            raise Warning('Checkout must be greater or equal checkin date')
        if self.checkin_date:
            diffDate = datetime.datetime(*time.strptime(self.checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(self.checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
            qty = diffDate.days
        self.product_uom_qty = qty
        
#completed but testing,,,,,--------need ?????!!! no onchnage in service line........................
#    def on_change_checkout(self, cr, uid, ids, checkin_date=None, checkout_date=None, context=None):
#        if not checkin_date:
#            checkin_date = time.strftime('%Y-%m-%d %H:%M:%S')
#        if not checkout_date:
#            checkout_date = time.strftime('%Y-%m-%d %H:%M:%S')
#        qty = 1
#        if checkout_date < checkin_date:
#            raise orm.except_orm(_('Error !'), _('Checkout must be greater or equal checkin date'))
#        if checkin_date:
#            diffDate = datetime.datetime(*time.strptime(checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
#            qty = diffDate.days
#        return {'value':{'product_uom_qty':qty}}

#    @api.multi 
#    def button_confirm(self):
#        line_ids = [folio.service_line_id.id for folio in self]
#        print "button confirm service line------- "
#        return self.env['sale.order.line'].button_confirm(line_ids)

#unused..............!!  
#    def button_confirm(self, cr, uid, ids, context=None):
#        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
#        return self.pool.get('sale.order.line').button_confirm(cr, uid, line_ids, context=context)

    #string not found.............
#    @api.multi
#    def button_done(self):
#        line_ids = [folio.service_line_id.id for folio in self]
#        print "button done service done"
#        return self.env['sale.order.line'].button_done(line_ids)

#unused..............!!
#    def button_done(self, cr, uid, ids, context=None):
#        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
#        return self.pool.get('sale.order.line').button_done(cr, uid, line_ids, context=context)


#    def uos_change(self, cr, uid, ids, product_uos, product_uos_qty=0, product_id=None):
#        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
#        return self.pool.get('sale.order.line').uos_change(cr, uid, line_ids, product_uos, product_uos_qty=0, product_id=None)

#on create error raise so how to check copy data..........!!!!!!!
#    def copy_data(self, cr, uid, id, default=None, context=None):
#        line_id = self.browse(cr, uid, id).service_line_id.id
#        return self.pool.get('sale.order.line').copy_data(cr, uid, line_id, default=default, context=context)


class hotel_service_type(models.Model):
    _name = "hotel.service.type"
    _description = "Service Type"
    
    ser_id = fields.Many2one('product.category','category', required=True, delegate=True, select=True, ondelete='cascade')


class hotel_services(models.Model):
    _name = 'hotel.services'
    _description = 'Hotel Services and its charges'
    
    service_id = fields.Many2one('product.product','Service_id',required=True, ondelete='cascade', delegate=True)

class res_company(models.Model):
    _inherit = 'res.company'

    additional_hours = fields.Integer('Additional Hours', help="Provide the min hours value for check in, checkout days, whatever the hours will be provided here based on that extra days will be calculated.")

## vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
