# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class ReportTestCheckin(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkin_qweb"

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

    def get_checkin(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkin', '>=', date_start),
                                      ('checkin', '<=', date_end)])
        return res

    @api.model
    def get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data == None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        folio_profile = self.env['hotel.reservation'].browse(docids)
        date_start = data.get('date_start', fields.Date.today())
        date_end = data['form'].get('date_end', str(datetime.now() +
                                    relativedelta(months=+1,
                                                  day=1, days=-1))[:10])
        rm_act = self.with_context(data['form'].get('used_context', {}))
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        get_checkin = rm_act.get_checkin(date_start, date_end)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_checkin': get_checkin,
        }


class ReportTestCheckout(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkout_qweb"

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

    def get_checkout(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkout', '>=', date_start),
                                      ('checkout', '<=', date_end)])
        return res

    @api.model
    def get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data == None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        folio_profile = self.env['hotel.reservation'].browse(docids)
        date_start = data.get('date_start', fields.Date.today())
        date_end = data['form'].get('date_end', str(datetime.now() +
                                    relativedelta(months=+1,
                                                  day=1, days=-1))[:10])
        rm_act = self.with_context(data['form'].get('used_context', {}))
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        get_checkout = rm_act.get_checkout(date_start, date_end)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_checkout': get_checkout,
        }


class ReportTestMaxroom(models.AbstractModel):
    _name = "report.hotel_reservation.report_maxroom_qweb"

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

    def get_data(self, date_start, date_end):
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
                for room_resv_line in room.room_reservation_line_ids:
                    if(room_resv_line.check_in >= date_start and
                       room_resv_line.check_in <= date_end):
                        counter += 1
            if counter >= 1:
                details.update({'name': room.name or '',
                                'no_of_times_used': counter})
                room_used_details.append(details)
        return room_used_details

    @api.model
    def get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data == None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        folio_profile = self.env['hotel.reservation'].browse(docids)
        date_start = data.get('date_start', fields.Date.today())
        date_end = data['form'].get('date_end', str(datetime.now() +
                                    relativedelta(months=+1,
                                                  day=1, days=-1))[:10])
        rm_act = self.with_context(data['form'].get('used_context', {}))
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        get_data = rm_act.get_data(date_start, date_end)
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
            'get_data': get_data,
            'get_room_used_detail': _get_room_used_detail,
        }


class ReportTestRoomres(models.AbstractModel):
    _name = "report.hotel_reservation.report_roomres_qweb"

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

    def get_data(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkin', '>=', date_start),
                                      ('checkout', '<=', date_end)])
        return res

    @api.model
    def get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data == None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        folio_profile = self.env['hotel.reservation'].browse(docids)
        date_start = data.get('date_start', fields.Date.today())
        date_end = data['form'].get('date_end', str(datetime.now() +
                                    relativedelta(months=+1,
                                                  day=1, days=-1))[:10])
        rm_act = self.with_context(data['form'].get('used_context', {}))
        _get_room_type = rm_act._get_room_type(date_start, date_end)
        _get_room_nos = rm_act._get_room_nos(date_start, date_end)
        get_data = rm_act.get_data(date_start, date_end)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_data': get_data,
        }
