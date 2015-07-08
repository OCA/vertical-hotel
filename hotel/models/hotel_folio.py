from openerp.osv import fields
import time
from openerp import netsvc, models, fields, api
import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import config
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools.translate import _


class HotelFolio(models.Model):
    _name = 'hotel.folio'
    _description = 'Hotel Folio'
    _inherits = {'sale.order': 'order_id'}
    _inherit = ['mail.thread']
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
        states={'draft': [('readonly', False)]})
    checkout_date = fields.Datetime(
        string='Check Out',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]})
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
    warehouse_id = fields.Many2one(
        'stock.warehouse')

    _sql_constraints = [
        ('check_in_out',
         'CHECK (checkin_date<=checkout_date)',
         'Check in Date Should be less than the Check Out Date!'), ]

    @api.onchange('checkin_date', 'checkout_date')
    def _onchange_dates(self):
        if self.checkin_date and self.checkout_date:
            checkin_date = datetime.datetime.strptime(
                self.checkin_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
            checkout_date = datetime.datetime.strptime(
                self.checkout_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
            duration_date = checkout_date - checkin_date
            duration = duration_date.days
            if self.duration != duration:
                self.duration = duration
            if self.checkout_date < self.checkin_date:
                raise Warning(
                    _('Check Out date can`t be previous than Check In date.'))

    @api.onchange('duration')
    def _onchange_duration(self):
        if self.checkin_date and self.duration:
            checkin_date = datetime.datetime.strptime(
                self.checkin_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
            duration = datetime.timedelta(days=self.duration)
            checkout_date = checkin_date + duration
            checkout_date = datetime.datetime.strftime(
                checkout_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
            if self.checkout_date != checkout_date:
                self.checkout_date = checkout_date

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.partner_invoice_id = self.partner_id.id
        self.partner_shipping_id = self.partner_id.id
        #partner_id = self.env['sale.order'].browse(self.ids)
        # return  partner_id.onchange_partner_id(part)

    @api.multi
    def button_dummy(self):
        dummy = self.env['sale.order'].browse(self.ids)
        return dummy.button_dummy()
        '''
        total_net = 0
        total_taxes = 0
        for room in  self.room_ids:
            checkin_date = datetime.datetime.strptime(
                room.checkin_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
            checkout_date = datetime.datetime.strptime(
                room.checkout_date,
                DEFAULT_SERVER_DATETIME_FORMAT) 
            duration_date = checkout_date - checkin_date
            duration = duration_date.days
            total_net += room.price_unit * duration
            print total_net
        self.amount_total = total_net
        return self.button_dummy()
        '''

    @api.multi
    def action_button_confirm(self):
        self.env['sale.order'].browse(self.ids).action_button_confirm()

    @api.multi
    def action_invoice_create(self, grouped=False, states=['confirmed', 'done']):
        i = self.env['sale.order'].browse(self.ids)
        i.action_invoice_create(grouped=False, states=['confirmed', 'done'])
        for line in self.browse(ids):
            self.write([line.id], {'invoiced': True})
            if grouped:
                self.write([line.id], {'state': 'progress'})
            else:
                self.write([line.id], {'state': 'progress'})
        return i

    @api.multi
    def action_invoice_cancel(self):
        res = self.env['sale.order'].browse(self.ids)
        res.action_invoice_cancel()
        for sale in self.browse(ids):
            for line in sale.order_line:
                self.env['sale.order.line'].write(
                    [line.id], {'invoiced': invoiced})
        self.write(ids, {'state': 'invoice_except', 'invoice_id': False})
        return res

    @api.multi
    def action_cancel(self):
        c = self.env['sale.order'].browse(self.ids)
        c.action_cancel()
        ok = True
        for sale in self.browse(self.ids):
            for r in self.read(['picking_ids']):
                for pick in r['picking_ids']:
                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate(
                        'stock.picking', pick, 'button_cancel')
            for r in self.read(['invoice_ids']):
                for inv in r['invoice_ids']:
                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate(
                        'account.invoice', inv, 'invoice_cancel')

        self.write({'state': 'cancel'})
        return c

    @api.multi
    def action_wait(self, *args):
        res = self.env['sale.order']
        res.action_wait(*args)
        for o in self.browse(self.ids):
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
            self.env['sale.order.line'].write(
                write_done_ids, {'state': 'done'})
        if write_cancel_ids:
            self.env['sale.order.line'].write(
                write_cancel_ids, {'state': 'cancel'})
        return res

    @api.multi
    def procurement_lines_get(self, *args):
        res = self.env['sale.order'].browse(
            self.ids).procurement_lines_get(*args)
        return res

    @api.multi
    def action_ship_create(self, *args):
        res = self.env['sale.order'].browse(self.ids).action_ship_create(*args)
        return res

    @api.multi
    def action_ship_end(self):
        res = self.env['sale.order'].browse(self.ids).action_ship_end()
        for order in self.browse(ids):
            val = {'shipped': True}
            self.write([order.id], val)
        return res

    @api.multi
    def _log_event(self, factor=0.7, name='Open Order'):
        event = self.env['sale.order'].browse(self.ids)
        return event._log_event(factor=0.7, name='Open Order')

    @api.multi
    def has_stockable_products(self, *args):
        products = self.env['sale.order'].browse(self.ids)
        return products.has_stockable_products(*args)

    @api.multi
    def action_cancel_draft(self, *args):
        d = self.env['sale.order'].browse(self.ids).action_cancel_draft(*args)
        self.write({'state': 'draft', 'invoice_ids': [], 'shipped': 0})
        self.env['sale.order.line'].write(
            {'invoiced': False, 'state': 'draft', 'invoice_lines': [(6, 0, [])]})
        return d

    # INHERIT METHODS FOR VIEWS
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        return self.pool['sale.order'].onchange_partner_id(cr,
                                                           uid,
                                                           [],
                                                           part,
                                                           context=context)

    def onchange_delivery_id(self, cr, uid, ids, company_id, partner_id,
                             delivery_id, fiscal_position, context=None):
        return self.pool['sale.order'].onchange_delivery_id(cr,
                                                            uid,
                                                            ids,
                                                            company_id,
                                                            partner_id,
                                                            delivery_id,
                                                            fiscal_position,
                                                            context=context)

    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id,
                              order_lines, context=None):
        return self.pool['sale.order'].onchange_pricelist_id(cr,
                                                             uid,
                                                             [],
                                                             pricelist_id,
                                                             order_lines,
                                                             context=context)

    def onchange_fiscal_position(self, cr, uid, ids, fiscal_position,
                                 order_lines, context=None):
        return self.pool['sale.order'].onchange_fiscal_position(cr,
                                                                uid,
                                                                [],
                                                                fiscal_position,
                                                                order_lines,
                                                                context=context)

    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id, context=None):
        return self.pool['sale.order'].onchange_warehouse_id(cr,
                                                             uid,
                                                             [],
                                                             warehouse_id,
                                                             context=context)
    def action_view_invoice(self, cr, uid, ids, context=None):
        folios = self.read(cr, uid, ids, ['order_id'], context=context)
        order_ids = [folio['order_id'] for folio in folios]
        return self.pool['sale.order'].action_view_invoice(cr,
                                                             uid,
                                                             order_ids,
                                                             context=context)
