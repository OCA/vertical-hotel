# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class FolioReport(models.AbstractModel):
    _name = "report.hotel.report_hotel_folio"
    _description = "Auxiliar to get the report"

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
        date_start = data["form"].get("date_start", fields.Date.today())
        date_end = data["form"].get(
            "date_end",
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10],
        )
        return {
            "doc_ids": docids,
            "doc_model": model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "folio_data": self._get_folio_data(date_start, date_end),
        }
