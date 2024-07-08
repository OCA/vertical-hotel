# Copyright (C) 2023-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class FolioReport(models.AbstractModel):
    _name = "report.hotel.report_hotel_folio"
    _description = "Auxiliar to get the report"

    def _convert_to_ist(self, utc_dt):
        user_tz = self._context.get("tz", "UTC")
        local_tz = pytz.timezone(user_tz)
        utc_tz = pytz.timezone("UTC")

        utc_dt = utc_tz.localize(utc_dt)
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt

    def _get_folio_data(self, date_start, date_end):
        total_amount = 0.0
        data_folio = []
        folio_obj = self.env["hotel.folio"]
        act_domain = [
            ("checkin_date", ">=", date_start),
            ("checkout_date", "<=", date_end),
        ]
        tids = folio_obj.search(act_domain)
        for data in tids:
            checkin = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(self, data.checkin_date)
            )
            checkout = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(self, data.checkout_date)
            )
            data_folio.append(
                {
                    "name": data.name,
                    "partner": data.partner_id.name,
                    "checkin": checkin,
                    "checkout": checkout,
                    "amount": data.amount_total,
                }
            )
            total_amount += data.amount_total
        data_folio.append({"total_amount": total_amount})
        return data_folio

    @api.model
    def _get_report_values(self, docids, data):
        model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.folio"].browse(docids)
        date_start_str = data["form"].get("date_start")
        date_end_str = data["form"].get("date_end")

        if not date_start_str:
            date_start_str = fields.Date.today().strftime("%Y-%m-%d 00:00:00")
        if not date_end_str:
            date_end_str = (
                datetime.now() + relativedelta(months=+1, day=1, days=-1)
            ).strftime("%Y-%m-%d 23:59:59")

        # Parse strings to datetime objects
        date_start_utc = datetime.strptime(date_start_str, "%Y-%m-%d %H:%M:%S")
        date_end_utc = datetime.strptime(date_end_str, "%Y-%m-%d %H:%M:%S")
        date_start_ist = self._convert_to_ist(date_start_utc)
        date_end_ist = self._convert_to_ist(date_end_utc)
        date_start = fields.Datetime.to_string(date_start_ist)
        date_end = fields.Datetime.to_string(date_end_ist)

        date_start_minus_5_30 = date_start_ist - timedelta(hours=5, minutes=30)
        date_end_minus_5_30 = date_end_ist - timedelta(hours=5, minutes=30)

        date_start_server = fields.Datetime.to_string(date_start_minus_5_30)
        date_end_server = fields.Datetime.to_string(date_end_minus_5_30)

        return {
            "doc_ids": docids,
            "doc_model": model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "folio_data": self._get_folio_data(date_start_server, date_end_server),
            "start_time": date_start,
            "end_time": date_end,
        }
