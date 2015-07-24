from openerp.osv import fields
import time
from openerp import netsvc, models, fields, api
from mx import DateTime
import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import config
from openerp.exceptions import except_orm
from openerp.exceptions import Warning
from openerp.exceptions import RedirectWarning
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


class HotelFolioRoom(models.Model):
    _name = 'hotel.folio.room'
    _description = 'Hotel Folio Room'


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


    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Order Line',
        required=True,
        ondelete='cascade',
        delegate=True)
    folio_id = fields.Many2one(
        'hotel.folio',
        string='Folio',
        ondelete='cascade',
        required=True)
    checkin_date = fields.Datetime(
        string='Check In',
        required=True)
    checkout_date = fields.Datetime(
        string='Check Out',
        required=True)

    _defaults = {
       'checkin_date':_get_checkin_date,
       'checkout_date':_get_checkout_date,
    }


    @api.model
    def create(self, vals, check=True):
        folio = self.env['hotel.folio'].browse([vals['folio_id']])[0]
        vals.update({'order_id':folio.order_id.id})
        return super(HotelFolioRoom, self).create(vals)


    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            if self.checkin_date and self.checkout_date:
                self.product_uom_qty = self._date_dif()
            else:
                self.product_uom_qty = 1
            if self.product_id.description:
                self.name = self.product_id.description
            else: self.name = self.product_id.name
            self.tax_id = self.product_id.taxes_id
            self.price_unit = self.product_id.list_price

            return self.pool['sale.order.line'].product_id_change(
                                        self._cr,
                                        self._uid,
                                        self._ids,
                                        self.folio_id.pricelist_id.id,
                                        self.product_id.id,
                                        self.product_uom_qty,
                                        False,
                                        self.product_uos_qty,
                                        False,
                                        self.product_id.name,
                                        self.folio_id.partner_id.id,
                                        False,
                                        True,
                                        self.folio_id.date_order,
                                        False,
                                        self.folio_id.partner_id
                                        .property_account_position.id,
                                        False,
                                        self._context)


    @api.onchange('checkin_date', 'checkout_date')
    def _onchange_dates(self):
        if self.checkin_date and self.checkout_date:
            duration = self._date_dif()
            if self.product_uom_qty != duration:
                self.product_uom_qty = duration
            if self.checkin_date > self.checkout_date:
                raise Warning(_('Check In can`t be higher than Check Out.'))


    @api.one
    @api.constrains('checkin_date','checkout_date','product_id')
    def _check_room_dates(self):
        if self.product_id.name != False:
            room_id = self.product_id.id

            rs = self.env['hotel.folio.room'].search_count([
                    '|', '&',
                    ('product_id', '=', room_id),
                    '&',
                    ('checkin_date', '<=', self.checkin_date),
                    ('checkout_date', '>=', self.checkin_date),
                    '|', '&',
                    ('product_id', '=', room_id),
                    '&',
                    ('checkout_date', '>=', self.checkout_date),
                    ('checkin_date', '<=', self.checkout_date),
                    '&',
                    ('product_id', '=', room_id),
                    '&',
                    ('checkin_date', '>=', self.checkin_date),
                    ('checkout_date', '<=', self.checkout_date)])

            if rs > 1:
                raise ValidationError(_('Your selected rooms are reserved for those \
                days. Please choose another dates.'))


    @api.onchange('product_uom_qty')
    def _onchange_duration(self):
        if self.checkin_date and self.product_uom_qty:
            checkin_date = datetime.datetime.strptime(
                self.checkin_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
            duration = datetime.timedelta(days=self.product_uom_qty)
            checkout_date = checkin_date + duration
            checkout_date = datetime.datetime.strftime(
                checkout_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
            if self.checkout_date != checkout_date:
                self.checkout_date = checkout_date


    def _date_dif(self):
        checkin_date = datetime.datetime.strptime(
                self.checkin_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
        checkout_date = datetime.datetime.strptime(
                self.checkout_date,
                DEFAULT_SERVER_DATETIME_FORMAT)
        duration_date = checkout_date - checkin_date
        duration = duration_date.days
        return duration


    @api.multi
    def on_change_checkout(self,
                           checkin_date=time.strftime('%Y-%m-%d %H:%M:%S'),
                           checkout_date=time.strftime('%Y-%m-%d %H:%M:%S')):
        qty = 1
        if checkout_date < checkin_date:
            raise osv.except_osv ('Error !', 'Checkout must be greater or \
            equal checkin date')
        if checkin_date:
            diffDate = datetime.datetime(*time.strptime(checkout_date,
                                                    '%Y-%m-%d %H:%M:%S')[:5])
            - datetime.datetime(*time.strptime(
                                        checkin_date,'%Y-%m-%d %H:%M:%S')[:5])
            qty = diffDate.days
            if qty == 0:
                qty = 1
        return {'value':{'product_uom_qty':qty}}


    @api.multi
    def button_confirm(self):
        return  self.button_confirm()


    @api.multi
    def button_done(self):
        res = self.env['sale.order.line'].browse(self.ids).button_done()
        wf_service = netsvc.LocalService("workflow")
        res = self.write({'state':'done'})
        for line in self.browse(ids):
            wf_service.trg_write(uid, 'sale.order', line.order_id.id, cr)
        return res


    @api.multi
    def unlink(self):
        if self.state not in ['draft', 'cancel']:
            raise Warning(_('Invalid Action!'),_('Cannot delete a sales order \
            line which is in state "%s".') %(self.state,))
        return super(HotelFolioRoom,self).unlink()


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
