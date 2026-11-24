# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HotelReservationWizard(models.TransientModel):
    _name = "hotel.reservation.wizard"
    _description = "Allow to generate a reservation"

    date_start = fields.Datetime("Start Date", required=True)
    date_end = fields.Datetime("End Date", required=True)

    def _print(self, report_xmlid):
        self.ensure_one()
        # plain values: the data goes through the client and the report URL
        data = {
            "form": {
                "date_start": fields.Datetime.to_string(self.date_start),
                "date_end": fields.Datetime.to_string(self.date_end),
            },
        }
        return self.env.ref(report_xmlid).report_action(self, data=data)

    def report_reservation_detail(self):
        return self._print("hotel_reservation.hotel_roomres_details")

    def report_checkin_detail(self):
        return self._print("hotel_reservation.hotel_checkin_details")

    def report_checkout_detail(self):
        return self._print("hotel_reservation.hotel_checkout_details")

    def report_maxroom_detail(self):
        return self._print("hotel_reservation.hotel_maxroom_details")

    @api.constrains("date_start", "date_end")
    def check_date(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError(
                    self.env._("End date must be Greater than the Start date")
                )
