# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models
import pytz

class FolioReport(models.AbstractModel):
    _name = 'report.hotel.report_hotel_folio'
    _description = 'Auxiliar to get the report'

    def _get_folio_data(self, date_start, date_end, user_lang, to_zone):
        total_amount = 0.0
        data_folio = []
        folio_obj = self.env['hotel.folio']
        act_domain = [('checkin_date', '>=', date_start),
                      ('checkout_date', '<=', date_end)]
        tids = folio_obj.search(act_domain)
        for data in tids:
            checkin = self.format_date(data.checkin_date, user_lang, to_zone)
            checkout = self.format_date(data.checkout_date, user_lang, to_zone)
            data_folio.append({
                'name': data.name,
                'partner': data.partner_id.name,
                'checkin': checkin,
                'checkout': checkout,
                'amount': data.amount_total
            })
            total_amount += data.amount_total
        data_folio.append({'total_amount': total_amount})
        return data_folio

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
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': folio_profile,
            'time': time,
            'folio_data': self._get_folio_data(date_start, date_end, user_lang, to_zone),
            'date_start': date_start_formatted,
            'date_end': date_end_formatted
        }
