# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models

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
    return datetime.strptime(_offset_format_timestamp1(time.strftime("%Y-%m-%d 15:00:00"),
                                     DEFAULT_SERVER_DATETIME_FORMAT,
                                     DEFAULT_SERVER_DATETIME_FORMAT,
                                     ignore_unparsable_time=True,
                                     context={'tz': to_zone}),
                                     '%Y-%m-%d %H:%M:%S')

def _get_checkout_date(self):
    if self._context.get('tz'):
        to_zone = self._context.get('tz')
    else:
        to_zone = 'UTC'
    tm_delta = timedelta(days=1)
    return datetime.strptime(_offset_format_timestamp1
                             (time.strftime("%Y-%m-%d 11:00:00"),
                              DEFAULT_SERVER_DATETIME_FORMAT,
                              DEFAULT_SERVER_DATETIME_FORMAT,
                              ignore_unparsable_time=True,
                              context={'tz': to_zone}),
                             '%Y-%m-%d %H:%M:%S') + tm_delta


class FolioReportWizard(models.TransientModel):
    _name = 'folio.report.wizard'
    _rec_name = 'date_start'
    _description = 'Allow print folio report by date'

    date_start = fields.Datetime('Start Date',
                              default=_get_checkin_date)
    date_end = fields.Datetime('End Date',
                              default=_get_checkout_date)

    @api.multi
    def print_report(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.folio',
            'form': self.read(['date_start', 'date_end'])[0]
        }
        return self.env.ref('hotel.report_hotel_management').\
            report_action(self, data=data)
