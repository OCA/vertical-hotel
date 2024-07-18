# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FolioReportWizard(models.TransientModel):
    _name = "folio.report.wizard"
    _rec_name = "date_start"
    _description = "Allow print folio report by date"

    date_start = fields.Datetime("Start Date")
    date_end = fields.Datetime("End Date")

    def print_report(self):
        data = {
            "ids": self.ids,
            "model": "hotel.folio",
            "form": self.read(["date_start", "date_end"])[0],
        }
        return self.env.ref("hotel.report_hotel_management").report_action(
            self, data=data
        )

    @api.model
    @api.constrains("date_start", "date_end")
    def check_date(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError(_("End date must be Greater than the Start date"))
