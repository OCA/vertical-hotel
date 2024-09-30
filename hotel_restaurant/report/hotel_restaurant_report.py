# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class HotelRestaurantReport(models.AbstractModel):
    _name = 'report.hotel_restaurant.report_res_table'

    def get_res_data(self, date_start, date_end):
        data = []
        rest_reservation_obj = self.env['hotel.restaurant.reservation']
        act_domain = [('start_date', '>=', date_start),
                      ('end_date', '<=', date_end)]
        tids = rest_reservation_obj.search(act_domain)
        for record in tids:
            data.append({
                'reservation': record.reservation_id,
                'name': record.cname.name,
                'start_date': (record.start_date).strftime('%m/%d/%Y'),
                'end_date': (record.end_date).strftime('%m/%d/%Y')})
        return data

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        folio_profile = self.env['hotel.restaurant.tables'].browse(docids)
        date_start = data.get('date_start', fields.Date.today())
        date_start = data.get('date_start', fields.Date.today())
        date_end = data['form'].get('date_end',
                                    str(datetime.now() +
                                        relativedelta(months=1,
                                                      day=1,
                                                      days=1))[:10])
        rm_act = self.with_context(data['form'].get('used_context', {}))
        reservation_res = rm_act.get_res_data(date_start, date_end)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'Reservations': reservation_res,
        }


class ReportKot(models.AbstractModel):
    _name = 'report.hotel_restaurant.report_hotel_order_kot'

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        folio_profile = self.env['hotel.restaurant.order'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'docs': folio_profile,
            'data': data,
        }


class FolioRestReport(models.AbstractModel):
    _name = 'report.hotel_restaurant.report_rest_order'

    def get_data(self, date_start, date_end):
        data = []
        act_domain = [('checkin_date', '>=', date_start),
                      ('checkout_date', '<=', date_end)]
        tids = self.env['hotel.folio'].search(act_domain)
        total = 0.0
        for record in tids:
            if record.hotel_reservation_order_ids:
                total_amount = 0.0
                total_order = 0
                for order in record.hotel_reservation_order_ids:
                    total_amount = total_amount + order.amount_total
                    total_order += 1
                total += total_amount
                data.append({
                    'folio_name': record.name,
                    'customer_name': record.partner_id.name,
                    'checkin_date': (record.checkin_date)
                    .strftime('%m/%d/%Y %H:%M:%S'),
                    'checkout_date': (record.checkout_date)
                    .strftime('%m/%d/%Y %H:%M:%S'),
                    'total_amount': total_amount,
                    'total_order': total_order})
        data.append({'total': total})
        return data

    def get_rest(self, date_start, date_end):
        data = []
        rest_domain = [('checkin_date', '>=', date_start),
                       ('checkout_date', '<=', date_end)]
        tids = self.env['hotel.folio'].search(rest_domain)
        for record in tids:
            if record.hotel_reservation_order_ids:
                order_data = []
                for order in record.hotel_reservation_order_ids:
                    order_data.append({
                        'order_no': order.order_number,
                        'order_date': (order.order_date)
                        .strftime('%m/%d/%Y %H:%M:%S'),
                        'state': order.state,
                        'table_no': len(order.table_no),
                        'order_len': len(order.order_list),
                        'amount_total': order.amount_total})
                data.append({'folio_name': record.name,
                             'customer_name': record.partner_id.name,
                             'order_data': order_data})
        return data

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        folio_profile = self.env['hotel.reservation.order'].browse(docids)
        date_start = data['form'].get('date_start', fields.Date.today())
        date_end = data['form'].get('date_end',
                                    str(datetime.now() +
                                        relativedelta(months=1,
                                                      day=1, days=1))[:10])
        rm_act = self.with_context(data['form'].get('used_context', {}))
        get_data_res = rm_act.get_data(date_start, date_end)
        get_rest_res = rm_act.get_rest(date_start, date_end)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'GetData': get_data_res,
            'GetRest': get_rest_res,
        }


class FolioReservReport(models.AbstractModel):
    _name = 'report.hotel_restaurant.report_reserv_order'

    def get_data(self, date_start, date_end):
        data = []
        folio_obj = self.env['hotel.folio']
        reserve_domain = [('checkin_date', '>=', date_start),
                          ('checkout_date', '<=', date_end)]
        tids = folio_obj.search(reserve_domain)
        total = 0.0
        for record in tids:
            if record.hotel_restaurant_order_ids:
                total_amount = 0.0
                total_order = 0
                for order in record.hotel_restaurant_order_ids:
                    total_amount = total_amount + order.amount_total
                    total_order += 1
                total += total_amount
                data.append({
                    'folio_name': record.name,
                    'customer_name': record.partner_id.name,
                    'checkin_date': (record.checkin_date).
                    strftime('%m/%d/%Y %H:%M:%S'),
                    'checkout_date': (record.checkout_date).
                    strftime('%m/%d/%Y %H:%M:%S'),
                    'total_amount': total_amount,
                    'total_order': total_order})
        data.append({'total': total})
        return data

    def get_reserv(self, date_start, date_end):
        data = []
        folio_obj = self.env['hotel.folio']
        res_domain = [('checkin_date', '>=', date_start),
                      ('checkout_date', '<=', date_end)]
        tids = folio_obj.search(res_domain)
        for record in tids:
            if record.hotel_restaurant_order_ids:
                order_data = []
                for order in record.hotel_restaurant_order_ids:
                    order_date = order.o_date
                    order_date = order_date.strftime('%m/%d/%Y %H:%M:%S')
                    order_data.append({'order_no': order.order_no,
                                       'order_date': order_date,
                                       'state': order.state,
                                       'room_no': order.room_no.name,
                                       'table_no': len(order.table_no),
                                       'amount_total': order.amount_total})
                data.append({'folio_name': record.name,
                             'customer_name': record.partner_id.name,
                             'order_data': order_data})
        return data

    @api.model
    def _get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data['form'].get('docids')
        folio_profile = self.env['hotel.restaurant.order'].browse(docids)
        date_start = data.get('date_start', fields.Date.today())
        date_end = data['form'].get('date_end',
                                    str(datetime.now() +
                                        relativedelta(months=1,
                                                      day=1, days=1))[:10])
        rm_act = self.with_context(data['form'].get('used_context', {}))
        get_data_res = rm_act.get_data(date_start, date_end)
        get_reserv_res = rm_act.get_reserv(date_start, date_end)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'GetData': get_data_res,
            'GetReserv': get_reserv_res,
        }
