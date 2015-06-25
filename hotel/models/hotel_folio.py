from openerp.osv import fields
import time
from openerp import netsvc, models, fields, api
from mx import DateTime
import datetime
from openerp.tools import config

class hotel_folio(models.Model):
    
    @api.model
    def _incoterm_get(self):
        return  self.env['sale.order']._incoterm_get()

    @api.one
    def copy(self):
        copy = self.env['sale.order'].browse(self.id)
        return  copy.copy(self)
    
    @api.multi
    def _invoiced(self, cursor, user, name, arg):
        invoiced = self.env['sale.order'].browse(self.ids)
        return  invoiced._invoiced(cursor, user, name, arg)

    @api.model
    def _invoiced_search(self, obj, name, args):
        return  self.env['sale.order']._invoiced_search(obj, name, args)

    @api.multi
    def _amount_untaxed(self, field_name, arg):
        sales = self.env['sale.order'].browse(self.ids)
        return sales._amount_untaxed(field_name, arg)
    
    @api.multi
    def _amount_tax(self, field_name, arg):
        amoun_tax = self.env['sale.order'].browse(self.ids)
        return amount_tax._amount_tax(field_name, arg)
    
    @api.multi
    def _amount_total(self, field_name, arg):
        amount = sel.env['sale.order'].browse(self.ids)
        return amount._amount_total(field_name, arg)
    
    _name = 'hotel.folio'
    
    _description = 'hotel folio new'
    
    _inherits = {'sale.order':'order_id'}
    
    _rec_name = 'order_id'
    
    order_id = fields.Many2one('sale.order', 'order_id', required=True, ondelete='cascade')
    checkin_date = fields.Datetime('Check In', required=True, readonly=True, states={'draft':[('readonly', False)]})
    checkout_date = fields.Datetime('Check Out', required=True, readonly=True, states={'draft':[('readonly', False)]})
    room_lines = fields.One2many('hotel.folio.line', 'folio_id')
    service_lines = fields.One2many('hotel.service.line', 'folio_id')
    hotel_policy = fields.Selection([('prepaid', 'On Booking'), ('manual', 'On Check In'), ('picking', 'On Checkout')], 'Hotel Policy', required=True)
    duration = fields.Float('Duration')

    _defaults = {
                 'hotel_policy':'manual'
                 }
    
    _sql_constraints = [
                        ('check_in_out', 'CHECK (checkin_date<=checkout_date)', 'Check in Date Should be less than the Check Out Date!'),
                       ]
    
    @api.multi
    def _check_room_vacant(self):
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
        vals['order_policy'] = vals.get('hotel_policy', 'manual')
        if not 'service_lines' and 'folio_id' in vals:
                vals.update({'room_lines':[]})
                folio = super(hotel_folio, self).create(vals)
                for line in (tmp_room_lines):
                    line[2].update({'folio_id':folio_id})
                vals.update({'room_lines':tmp_room_lines})
                folio.write(vals)
        else:
            folio_id = super(hotel_folio, self).create(vals)
        return folio_id
    
    @api.multi
    def onchange_shop_id(self, shop_id):
        shop_id = self.env['sale.order'].browse(self.ids)
        return  shop_id.onchange_shop_id(shop_id)
    
    @api.multi
    def onchange_partner_id(self, part):
        partner_id = self.env['sale.order'].browse(self.ids)
        return  partner_id.onchange_partner_id(part)
    
    @api.multi
    def button_dummy(self):
        dummy = self.env['sale.order'].browse(self.ids)
        return  dummy.button_dummy()
    
    @api.multi
    def action_invoice_create(self, grouped=False, states=['confirmed', 'done']):
        i = self.env['sale.order'].browse(self.ids)
        i.action_invoice_create(grouped=False, states=['confirmed', 'done'])
        for line in self.browse(ids):
            self.write([line.id], {'invoiced':True})
            if grouped:
               self.write([line.id], {'state' : 'progress'})
            else:
               self.write([line.id], {'state' : 'progress'})
        return i 

    @api.multi
    def action_invoice_cancel(self):
        res = self.env['sale.order'].browse(self.ids)
        res.action_invoice_cancel()
        for sale in self.browse(ids):
            for line in sale.order_line:
                self.env['sale.order.line'].write([line.id], {'invoiced': invoiced})
        self.write(ids, {'state':'invoice_except', 'invoice_id':False})
        return res  
    
    @api.multi
    def action_cancel(self):
        c = self.env['sale.order'].browse(self.ids)
        c.action_cancel()
        ok = True
        for sale in self.browse(ids):
            for r in self.read(['picking_ids']):
                for pick in r['picking_ids']:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate('stock.picking', pick, 'button_cancel')
            for r in self.read(['invoice_ids']):
                for inv in r['invoice_ids']:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate('account.invoice', inv, 'invoice_cancel')
            
        self.write({'state':'cancel'})
        return c
    
    @api.multi
    def action_wait(self, *args):
        res = self.env['sale.order']
        res.action_wait(*args)
        for o in self.browse(ids):
            if (o.order_policy == 'manual') and (not o.invoice_ids):
                self.write([o.id], {'state': 'manual'})
            else:
                self.write([o.id], {'state': 'progress'})
        return res
    
    @api.multi
    def test_state(self, mode, *args):
        write_done_ids = []
        write_cancel_ids = []
        res = self.env['sale.order']
        res.test_state(mode, *args)
        if write_done_ids:
            self.env['sale.order.line'].write(write_done_ids, {'state': 'done'})
        if write_cancel_ids:
            self.env['sale.order.line'].write(write_cancel_ids, {'state': 'cancel'})
        return res 
    
    @api.multi
    def procurement_lines_get(self, *args):
        res = self.env['sale.order'].browse(self.ids).procurement_lines_get(*args)
        return  res
    
    @api.multi
    def action_ship_create(self, *args):
        res = self.env['sale.order'].browse(self.ids).action_ship_create(*args)
        return res
    
    @api.multi
    def action_ship_end(self):
        res = self.env['sale.order'].browse(self.ids).action_ship_end()
        for order in self.browse(ids):
            val = {'shipped':True}
            self.write([order.id], val)
        return res 
    
    @api.multi
    def _log_event(self, factor=0.7, name='Open Order'):
       event = self.env['sale.order'].browse(self.ids)
       return  event._log_event(factor=0.7, name='Open Order')
    
    @api.multi
    def has_stockable_products(self, *args):
        products = self.env['sale.order'].browse(self.ids)
        return products.has_stockable_products(*args)
    
    @api.multi
    def action_cancel_draft(self, *args):
        d = self.env['sale.order'].browse(self.ids).action_cancel_draft(*args)
        self.write({'state':'draft', 'invoice_ids':[], 'shipped':0})
        self.env['sale.order.line'].write({'invoiced':False, 'state':'draft', 'invoice_lines':[(6, 0, [])]})
        return d

class hotel_folio_line(models.Model):
    
    @api.one
    def copy(self, default=None):
        copy = self.env['sale.order.line'].browse(self.id)
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
    
    @api.model
    def _get_checkin_date(self):
        if 'checkin_date' in self._context:
            return self._context['checkin_date']
        return time.strftime('%Y-%m-%d %H:%M:%S')
    
    @api.model
    def _get_checkout_date(self):
        if 'checkin_date' in self._context:
            return self._context['checkout_date']
        return time.strftime('%Y-%m-%d %H:%M:%S')
 
    _name = 'hotel.folio.line'
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
        if not self._context:
            self._context = {}
        if vals.has_key("folio_id"):
            folio = self.env['hotel.folio'].browse([vals['folio_id']])[0]
            vals.update({'order_id':folio.order_id.id})
        roomline = super(models.Model, self).create(vals)
        return roomline
    
    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        line_ids = [folio.order_line_id.id for folio in self]
        change = self.env['sale.order.line'].browse(line_ids)
        return  change.uos_change(product_uos, product_uos_qty=0, product_id=None)
    
    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        line_ids = [folio.order_line_id.id for folio in self]
        if product:
            return self.env['sale.order.line'].browse(line_ids).product_id_change(pricelist, 
                product, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
                lang=False, update_tax=True, date_order=False)
    
    @api.multi    
    def product_uom_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        if product:
            return self.product_id_change( pricelist, product, qty=0,
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
        confirm = self.env['sale.order.line'].browse(selfids)
        return  confirm.button_confirm()
    
    @api.multi
    def button_done(self):
        res = self.env['sale.order.line'].browse(self.ids).button_done()
        wf_service = netsvc.LocalService("workflow")
        res = self.write({'state':'done'})
        for line in self.browse(ids):
            wf_service.trg_write(uid, 'sale.order', line.order_id.id, cr)
        return res

    @api.multi    
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        change = self.env['sale.order.line'].browse(self.ids)
        return  change.uos_change(product_uos, product_uos_qty=0, product_id=None)
    
    @api.one
    def copy(self, default=None):
        copy = self.env['sale.order.line'].browse(self.id)
        return  copy.copy(default=None)
