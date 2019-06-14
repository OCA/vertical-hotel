# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz

class ReportTestCheckin(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkin_qweb"
    _description = 'Auxiliar to get the check in report'

    def _get_room_type(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        room_dom = [('checkin', '>=', date_start),
                    ('checkout', '<=', date_end)]
        res = reservation_obj.search(room_dom)
        return res

    def _get_room_nos(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkin', '>=', date_start),
                                      ('checkout', '<=', date_end)])
        return res

    def get_checkin(self, date_start, date_end, user_lang, to_zone):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkin', '>=', date_start),
                                      ('checkin', '<=', date_end)])
        new_res = []
        for reservation in res:
            new_checkin = self.format_date(reservation.checkin, user_lang, to_zone)
            new_res.append({'reservation_no': reservation.reservation_no,
                            'checkin': new_checkin,
                            'partner_id': reservation.partner_id,
                            'reservation_line': reservation.reservation_line,
                            })
        return new_res

    def format_date(self, date, user_lang, to_zone):
        if isinstance(date, str):
            new_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        else:
            new_date = date
        timezone_conv = pytz.timezone(to_zone)
        timezone_utc = pytz.timezone('UTC')
        new_date = timezone_utc.localize(new_date)
        new_date = new_date.astimezone(timezone_conv)
        date_converted = new_date.strftime(user_lang.date_format+" "+user_lang.time_format)
        return date_converted
    
    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        context = self._context
        current_uid = context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        user_lang = self.env['res.lang'].search([('code', '=', user.lang)])[0]
        if self._context.get('tz'):
            to_zone = self._context.get('tz')
        else:
            to_zone = 'UTC'
        rm_act = self.with_context(data['form'].get('used_context', {}))
        folio_profile = self.env['hotel.reservation'].browse(docids)
        date_start = data['form'].get('date_start', str(datetime.now())[:10])
        date_end = data['form'].get('date_end', str(datetime.now() +
                                    relativedelta(months=+1,
                                                  day=1, days=-1))[:10])
        date_start_formatted = rm_act.format_date(date_start, user_lang, to_zone)
        date_end_formatted = rm_act.format_date(date_end, user_lang, to_zone)
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        get_checkin = rm_act.get_checkin(date_start, date_end, user_lang, to_zone)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_checkin': get_checkin,
            'date_start': date_start_formatted,
            'date_end': date_end_formatted
        }


class ReportTestCheckout(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkout_qweb"
    _description = 'Auxiliar to get the check out report'

    def _get_room_type(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkout', '>=', date_start),
                                      ('checkout', '<=', date_end)])
        return res

    def _get_room_nos(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkout', '>=', date_start),
                                      ('checkout', '<=', date_end)])
        return res

    def _get_checkout(self, date_start, date_end, user_lang, to_zone):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkout', '>=', date_start),
                                      ('checkout', '<=', date_end)])
        new_res = []
        for reservation in res:
            new_checkout = self.format_date(reservation.checkout, user_lang, to_zone)
            new_res.append({'reservation_no': reservation.reservation_no,
                            'checkout': new_checkout,
                            'partner_id': reservation.partner_id,
                            'reservation_line': reservation.reservation_line,
                            })
        return new_res

    def format_date(self, date, user_lang, to_zone):
        if isinstance(date, str):
            new_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        else:
            new_date = date
        timezone_conv = pytz.timezone(to_zone)
        timezone_utc = pytz.timezone('UTC')
        new_date = timezone_utc.localize(new_date)
        new_date = new_date.astimezone(timezone_conv)
        date_converted = new_date.strftime(user_lang.date_format+" "+user_lang.time_format)
        return date_converted

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        context = self._context
        current_uid = context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        user_lang = self.env['res.lang'].search([('code', '=', user.lang)])[0]
        if self._context.get('tz'):
            to_zone = self._context.get('tz')
        else:
            to_zone = 'UTC'
        rm_act = self.with_context(data['form'].get('used_context', {}))
        folio_profile = self.env['hotel.reservation'].browse(docids)
        date_start = data['form'].get('date_start', str(datetime.now())[:10])
        date_end = data['form'].get('date_end', str(datetime.now() +
                                    relativedelta(months=+1,
                                                  day=1, days=-1))[:10])
        date_start_formatted = rm_act.format_date(date_start, user_lang, to_zone)
        date_end_formatted = rm_act.format_date(date_end, user_lang, to_zone)
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        get_checkout = rm_act._get_checkout(date_start, date_end, user_lang, to_zone)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_checkout': get_checkout,
            'date_start': date_start_formatted,
            'date_end': date_end_formatted
        }


class ReportTestMaxroom(models.AbstractModel):
    _name = "report.hotel_reservation.report_maxroom_qweb"
    _description = 'Auxiliar to get the room report'

    def _get_room_type(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        tids = reservation_obj.search([('checkin', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(tids)
        return res

    def _get_room_nos(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        tids = reservation_obj.search([('checkin', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(tids)
        return res

    def _get_data(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkin', '>=', date_start),
                                      ('checkout', '<=', date_end)])
        return res

    def _get_room_used_detail(self, date_start, date_end):
        room_used_details = []
        hotel_room_obj = self.env['hotel.room']
        room_ids = hotel_room_obj.search([])
        for room in hotel_room_obj.browse(room_ids.ids):
            counter = 0
            details = {}
            if room.room_reservation_line_ids:
                end_date = datetime.strptime(date_end,
                                             DEFAULT_SERVER_DATETIME_FORMAT)
                start_date = datetime.strptime(date_start,
                                               DEFAULT_SERVER_DATETIME_FORMAT)
                for room_resv_line in room.room_reservation_line_ids:
                    if(room_resv_line.check_in >= start_date and
                       room_resv_line.check_in <= end_date):
                        counter += 1
            if counter >= 1:
                details.update({'name': room.name or '',
                                'no_of_times_used': counter})
                room_used_details.append(details)
        return room_used_details

    def format_date(self, date, user_lang, to_zone):
        if isinstance(date, str):
            new_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        else:
            new_date = date
        timezone_conv = pytz.timezone(to_zone)
        timezone_utc = pytz.timezone('UTC')
        new_date = timezone_utc.localize(new_date)
        new_date = new_date.astimezone(timezone_conv)
        date_converted = new_date.strftime(user_lang.date_format+" "+user_lang.time_format)
        return date_converted

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        context = self._context
        current_uid = context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        user_lang = self.env['res.lang'].search([('code', '=', user.lang)])[0]
        if self._context.get('tz'):
            to_zone = self._context.get('tz')
        else:
            to_zone = 'UTC'
        rm_act = self.with_context(data['form'].get('used_context', {}))
        folio_profile = self.env['hotel.reservation'].browse(docids)
        date_start = data['form'].get('date_start', str(datetime.now())[:10])
        date_end = data['form'].get('date_end', str(datetime.now() +
                                    relativedelta(months=+1,
                                                  day=1, days=-1))[:10])
        date_start_formatted = rm_act.format_date(date_start, user_lang, to_zone)
        date_end_formatted = rm_act.format_date(date_end, user_lang, to_zone)
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        _get_data = rm_act._get_data(date_start, date_end)
        _get_room_used_detail = rm_act._get_room_used_detail(date_start,
                                                             date_end)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_data': _get_data,
            'get_room_used_detail': _get_room_used_detail,
            'date_start': date_start_formatted,
            'date_end': date_end_formatted
        }


class ReportTestRoomres(models.AbstractModel):
    _name = "report.hotel_reservation.report_roomres_qweb"
    _description = 'Auxiliar to get the room report'

    def _get_room_type(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        tids = reservation_obj.search([('checkin', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(tids)
        return res

    def _get_room_nos(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        tids = reservation_obj.search([('checkin', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(tids)
        return res

    def _get_data(self, date_start, date_end, user_lang, to_zone):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkin', '>=', date_start),
                                      ('checkout', '<=', date_end)])
        new_res = []
        for reservation in res:
            new_checkout = self.format_date(reservation.checkout, user_lang, to_zone)
            new_checkin = self.format_date(reservation.checkin, user_lang, to_zone)
            new_res.append({'reservation_no': reservation.reservation_no,
                            'checkout': new_checkout,
                            'checkin': new_checkin,
                            'partner_id': reservation.partner_id,
                            'reservation_line': reservation.reservation_line,
                            })
        return new_res

    def format_date(self, date, user_lang, to_zone):
        if isinstance(date, str):
            new_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        else:
            new_date = date
        timezone_conv = pytz.timezone(to_zone)
        timezone_utc = pytz.timezone('UTC')
        new_date = timezone_utc.localize(new_date)
        new_date = new_date.astimezone(timezone_conv)
        date_converted = new_date.strftime(user_lang.date_format+" "+user_lang.time_format)
        return date_converted

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        context = self._context
        current_uid = context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        user_lang = self.env['res.lang'].search([('code', '=', user.lang)])[0]
        if self._context.get('tz'):
            to_zone = self._context.get('tz')
        else:
            to_zone = 'UTC'
        rm_act = self.with_context(data['form'].get('used_context', {}))
        folio_profile = self.env['hotel.reservation'].browse(docids)
        date_start = data['form'].get('date_start', str(datetime.now())[:10])
        date_end = data['form'].get('date_end', str(datetime.now() +
                                    relativedelta(months=+1,
                                                  day=1, days=-1))[:10])
        date_start_formatted = rm_act.format_date(date_start, user_lang, to_zone)
        date_end_formatted = rm_act.format_date(date_end, user_lang, to_zone)
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        _get_data = rm_act._get_data(date_start, date_end, user_lang, to_zone)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_data': _get_data,
            'date_start': date_start_formatted,
            'date_end': date_end_formatted
        }
