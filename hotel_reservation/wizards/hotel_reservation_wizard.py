# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from odoo.exceptions import ValidationError

def _offset_format_timestamp1(src_tstamp_str, src_format, dst_format,
                              ignore_unparsable_time=True, context=None):
    """
    Convert a source timeStamp string into a destination timeStamp string,
    attempting to apply the correct offset if both the server and local
    timeZone are recognized,or no offset at all if they aren't or if
    tz_offset is false (i.e. assuming they are both in the same TZ).

    @param src_tstamp_str: the STR value containing the timeStamp.
    @param src_format: the format to use when parsing the local timeStamp.
    @param dst_format: the format to use when formatting the resulting
     timeStamp.
    @param server_to_client: specify timeZone offset direction (server=src
                             and client=dest if True, or client=src and
                             server=dest if False)
    @param ignore_unparsable_time: if True, return False if src_tstamp_str
                                   cannot be parsed using src_format or
                                   formatted using dst_format.
    @return: destination formatted timestamp, expressed in the destination
             timezone if possible and if tz_offset is true, or src_tstamp_str
             if timezone offset could not be determined.
    """
    if not src_tstamp_str:
        return False
    res = src_tstamp_str
    if src_format and dst_format:
        try:
            # dt_value needs to be a datetime object\
            # (so notime.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.strptime(src_tstamp_str, src_format)
            if context.get('tz', False):
                try:
                    import pytz
                    src_tz = pytz.timezone(context['tz'])
                    dst_tz = pytz.timezone('UTC')
                    src_dt = src_tz.localize(dt_value, is_dst=True)
                    dt_value = src_dt.astimezone(dst_tz)
                except Exception:
                    pass
            res = dt_value.strftime(dst_format)
        except Exception:
            # Normal ways to end up here are if strptime or strftime failed
            if not ignore_unparsable_time:
                return False
            pass
    return res

def _get_checkin_date(self):
    if self._context.get('tz'):
        to_zone = self._context.get('tz')
    else:
        to_zone = 'UTC'
    return datetime.strptime(_offset_format_timestamp1
                             (time.strftime("%Y-%m-%d 15:00:00"),
                              DEFAULT_SERVER_DATETIME_FORMAT,
                              '%m/%d/%Y %H:%M:%S',
                              ignore_unparsable_time=True,
                              context={'tz': to_zone}),
                             '%m/%d/%Y %H:%M:%S')

def _get_checkout_date(self):
    if self._context.get('tz'):
        to_zone = self._context.get('tz')
    else:
        to_zone = 'UTC'
    tm_delta = timedelta(days=1)
    return datetime.strptime(_offset_format_timestamp1
                             (time.strftime("%Y-%m-%d 11:00:00"),
                              DEFAULT_SERVER_DATETIME_FORMAT,
                              '%m/%d/%Y %H:%M:%S',
                              ignore_unparsable_time=True,
                              context={'tz': to_zone}),
                             '%m/%d/%Y %H:%M:%S') + tm_delta

class HotelReservationWizard(models.TransientModel):
    _name = 'hotel.reservation.wizard'
    _description = 'Allow to generate a reservation'

    date_start = fields.Datetime('Start Date', required=True, default=_get_checkin_date)
    date_end = fields.Datetime('End Date', required=True, default=_get_checkout_date)

    @api.multi
    def report_reservation_detail(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.reservation',
            'form': self.read(['date_start', 'date_end'])[0]
        }
        return self.env.ref('hotel_reservation.hotel_roomres_details'
                            ).report_action(self, data=data)

    @api.multi
    def report_checkin_detail(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.reservation',
            'form': self.read(['date_start', 'date_end'])[0],
        }
        return self.env.ref('hotel_reservation.hotel_checkin_details'
                            ).report_action(self, data=data)

    @api.multi
    def report_checkout_detail(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.reservation',
            'form': self.read(['date_start', 'date_end'])[0]
        }
        return self.env.ref('hotel_reservation.hotel_checkout_details'
                            ).report_action(self, data=data)

    @api.multi
    def report_maxroom_detail(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.reservation',
            'form': self.read(['date_start', 'date_end'])[0]
        }
        return self.env.ref('hotel_reservation.hotel_maxroom_details'
                            ).report_action(self, data=data)


class MakeFolioWizard(models.TransientModel):
    _name = 'wizard.make.folio'
    _description = 'Allow to generate the folio'

    grouped = fields.Boolean('Group the Folios')

    @api.multi
    def create_folio(self):
        """
        This method is for create new hotel folio.
        -----------------------------------------
        @param self: The object pointer
        @return: new record set for hotel folio.
        """
        hotel_folio_obj = self.env['hotel.folio']
        room_obj = self.env['hotel.room']
        reservation_ids = self.env['hotel.reservation'].browse(self._context.get('active_ids'))
        if len(reservation_ids) >= 1:
            reservation = reservation_ids[0]
            folio_lines = []
            checkin_date = reservation['checkin']
            checkout_date = reservation['checkout']
            for res in reservation_ids:
                if res.state != 'confirm':
                    raise ValidationError(_('Reservations must be in "Confirm" state to be added to a folio.'))
                if not res.checkin < res.checkout:
                    raise ValidationError(_('Checkout date should be greater \
                                         than the Check-in date.'))
            duration_vals = (reservation.onchange_check_dates
                             (checkin_date=checkin_date,
                              checkout_date=checkout_date, duration=False))
            duration = duration_vals.get('duration') or 0.0
            folio_vals = {
                'date_order': reservation.date_order,
                'warehouse_id': reservation.warehouse_id.id,
                'partner_id': reservation.partner_id.id,
                'pricelist_id': reservation.pricelist_id.id,
                'partner_invoice_id': reservation.partner_invoice_id.id,
                'partner_shipping_id': reservation.partner_shipping_id.id,
                'duration': duration,
                'reservation_id': reservation.id,
                'service_lines': reservation['folio_id']
            }
            final_checkin = None
            final_checkout = None
            for res in reservation_ids:
                if (final_checkin is None) or (res.checkin < final_checkin):
                    final_checkin = res.checkin
                if (final_checkout is None) or (res.checkout > final_checkout):
                    final_checkout = res.checkout
                for line in res.reservation_line:
                    for r in line.reserve:
                        duration_vals = (res.onchange_check_dates
                        (checkin_date=checkin_date,
                         checkout_date=checkout_date, duration=False))
                        duration = duration_vals.get('duration') or 0.0
                        checkin_date = res['checkin']
                        checkout_date = res['checkout']
                        folio_lines.append((0, 0, {
                            'checkin_date': checkin_date,
                            'checkout_date': checkout_date,
                            'product_id': r.product_id and r.product_id.id,
                            'name': res['reservation_no'],
                            'price_unit': r.list_price,
                            'product_uom_qty': duration,
                            'is_reserved': True,
                            'reservation' : res.id}))
                        res_obj = room_obj.browse([r.id])
                        res_obj.write({'status': 'occupied', 'isroom': False})
                res.state = 'done'
            folio_vals.update({'room_lines': folio_lines, 'checkin_date': final_checkin, 'checkout_date': final_checkout})
            folio = hotel_folio_obj.create(folio_vals)
            if folio:
                for rm_line in folio.room_lines:
                    rm_line.product_id_change()
            self._cr.execute('insert into hotel_folio_reservation_rel'
                             '(order_id, invoice_id) values (%s,%s)',
                             (reservation.id, folio.id))
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hotel.folio',
                'res_id': folio.id,
                'type': 'ir.actions.act_window'
            }
