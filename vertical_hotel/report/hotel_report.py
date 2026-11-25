# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class FolioReport(models.AbstractModel):
    _name = "report.vertical_hotel.report_hotel_folio"
    _description = "Auxiliar to get the report"

    def _get_folio_data(self, date_start, date_end):
        total_amount = 0.0
        data_folio = []
        folios = self.env["hotel.folio"].search(
            [
                ("checkin_date", ">=", date_start),
                ("checkout_date", "<=", date_end),
            ],
            order="checkin_date, id",
        )
        for folio in folios:
            room_lines = folio.room_line_ids
            data_folio.append(
                {
                    "name": folio.name,
                    "partner": folio.partner_id.name,
                    "checkin": min(room_lines.mapped("checkin_date"), default=None)
                    or folio.checkin_date,
                    "checkout": max(room_lines.mapped("checkout_date"), default=None)
                    or folio.checkout_date,
                    "amount": folio.amount_total,
                }
            )
            total_amount += folio.amount_total
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
            str(fields.Datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10],
        )
        return {
            "doc_ids": docids,
            "doc_model": model,
            "data": data["form"],
            "docs": folio_profile,
            "time": time,
            "folio_data": self._get_folio_data(date_start, date_end),
        }
