# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HotelHousekeepingWizard(models.TransientModel):
    _name = "hotel.housekeeping.wizard"
    _description = "Hotel Housekeeping Wizard"

    date_start = fields.Datetime("Activity Start Date", required=True)
    date_end = fields.Datetime("Activity End Date", required=True)
    room_id = fields.Many2one("hotel.room", "Room No", required=True)

    def print_report(self):
        data = {
            "ids": self.ids,
            "model": "hotel.housekeeping",
            "form": self.read(["date_start", "date_end", "room_id"])[0],
        }
        return self.env.ref(
            "hotel_housekeeping.report_hotel_housekeeping"
        ).report_action(self, data=data)

    @api.constrains("date_start", "date_end")
    def check_date(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError(_("End date must be Greater than the Start date"))
