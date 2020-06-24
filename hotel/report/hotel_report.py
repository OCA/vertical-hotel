# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime

from dateutil import parser
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class FolioReport(models.AbstractModel):
    _name = "report.hotel.report_hotel_folio"

    def get_data(self, date_start, date_end):
        total_amount = 0.0
        data_folio = []
        folio_obj = self.env["hotel.folio"]
        act_domain = [
            ("checkin_date", ">=", date_start),
            ("checkout_date", "<=", date_end),
        ]
        tids = folio_obj.search(act_domain)
        for data in tids:
            data_folio.append(
                {
                    "name": data.name,
                    "partner": data.partner_id.name,
                    "checkin": parser.parse(data.checkin_date).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    ),
                    "checkout": parser.parse(data.checkout_date).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT
                    ),
                    "amount": data.amount_total,
                }
            )
            total_amount += data.amount_total
        data_folio.append({"total_amount": total_amount})
        return data_folio

    @api.model
    def get_report_values(self, docids, data):
        self.model = self.env.context.get("active_model")
        if data is None:
            data = {}
        if not docids:
            docids = data["form"].get("docids")
        folio_profile = self.env["hotel.folio"].browse(docids)
        date_start = data["form"].get("date_start", fields.Date.today())
        date_end = data["form"].get(
            "date_end",
            str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[
                :10
            ],
        )
        return {
            "doc_ids": docids,
            "doc_model": self.model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "folio_data": self.get_data(date_start, date_end),
        }
