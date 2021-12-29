# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class FolioReportWizard(models.TransientModel):
    _name = "folio.report.wizard"
    _rec_name = "date_start"
    _description = "Allow print folio report by date"

    date_start = fields.Datetime("Start Date")
    date_end = fields.Datetime("End Date")

    @api.multi
    def print_report(self):
        date_data = self.read(["date_start", "date_end"])[0]
        date_start = fields.Datetime.to_string(
            fields.Datetime.context_timestamp(
                self, date_data.get("date_start")
            )
        )
        date_end = fields.Datetime.to_string(
            fields.Datetime.context_timestamp(self, date_data.get("date_end"))
        )
        date_data.update({"date_start": date_start, "date_end": date_end})
        data = {"ids": self.ids, "model": "hotel.folio", "form": date_data}
        return self.env.ref("hotel.report_hotel_management").report_action(
            self, data=data
        )
