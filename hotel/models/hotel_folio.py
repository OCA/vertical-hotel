from openerp.osv import fields
import time
from openerp import netsvc, models, fields, api
import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import config

class HotelFolio(models.Model):
    _name = 'hotel.folio'
    _description = 'Hotel Folio'
    _inherits = {'sale.order':'order_id'}
    _rec_name = 'order_id'
    _order_id = 'id desc'
    
    order_id = fields.Many2one(
        'sale.order',
        string='Order',
        required=True,
        ondelete='cascade')
    checkin_date = fields.Datetime(
        string='Check In',
        required=True,
        readonly=True,
        states={'draft':[('readonly', False)]})
    checkout_date = fields.Datetime(
        string='Check Out',
        required=True,
        readonly=True,
        states={'draft':[('readonly', False)]})
    room_ids = fields.One2many(
        'hotel.folio.room',
        'folio_id',
        string='Rooms')
    service_ids = fields.One2many(
        'hotel.folio.service',
        'folio_id',
        string='Services')
    hotel_policy = fields.Selection(
        [('prepaid', 'On Booking'),
         ('manual', 'On Check In'),
         ('picking', 'On Checkout')],
        string='Hotel Policy',
        default='manual',
        required=True)
    duration = fields.Float(
        string='Duration')

    
    _sql_constraints = [
        ('check_in_out',
         'CHECK (checkin_date<=checkout_date)',
         'Check in Date Should be less than the Check Out Date!'),]
    
    @api.one
    @api.constrains('room_ids')
    def _check_room_vacant(self):
        rooms = []
        for room in self.room_ids:
            if room.product_id in rooms:
                raise ValidationError('You can not allocate the same room twice!')
            rooms.append(room.product_id)

    @api.onchange('checkin_date', 'checkout_date')
    def _onchange_dates(self):
        if self.checkin_date and checkout_date:
            checkin_date = datetime.datetime.strptime(
                self.checkin_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
            checkout_date = datetime.datetime.strptime(
                self.checkout_date,
                DEFAULT_SERVER_DATETIME_FORMAT) 
            duration_date = checkin_date - checkout_date
            duration = duration_date.days
            if self.duration != duration:
                self.duration = duration 
    
    
    @api.onchange('duration')
    def _onchange_duration(self):
        if self.checkin_date and self.duration:
            checkin_date = datetime.datetime.strptime(
                checkin_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
            duration = datetime.timedelta(days=self.duration)
            checkout_date = checkin_date + duration
            checkout_date = datetime.datetime.strftime(
                checkout_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
            if self.checkout_date != checkout_date:
                self.checkout_date = checkout_date

    
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
                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate('stock.picking', pick, 'button_cancel')
            for r in self.read(['invoice_ids']):
                for inv in r['invoice_ids']:
                    wf_service = netsvc.LocalService('workflow')
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
