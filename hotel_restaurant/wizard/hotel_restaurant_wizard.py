# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class WizardHotelRestaurant(models.TransientModel):
    _name = "wizard.hotel.restaurant"
    _description = "wizard.hotel.restaurant"

    date_start = fields.Datetime("Start Date", required=True)
    date_end = fields.Datetime("End Date", required=True)

    def print_report(self):
        self.ensure_one()
        # plain values: the data goes through the client and the report URL
        data = {
            "form": {
                "date_start": fields.Datetime.to_string(self.date_start),
                "date_end": fields.Datetime.to_string(self.date_end),
            }
        }
        return self.env.ref("hotel_restaurant.report_hotel_table_res").report_action(
            self, data=data
        )

    @api.constrains("date_start", "date_end")
    def check_date(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError(
                    self.env._("End date must be Greater than the Start date")
                )


class FolioRestReservation(models.TransientModel):
    _name = "folio.rest.reservation"
    _description = "folio.rest.reservation"
    _rec_name = "date_start"

    date_start = fields.Datetime("Start Date", required=True)
    date_end = fields.Datetime("End Date", required=True)
    check = fields.Boolean("With Details")

    def _print(self, report_xmlid):
        self.ensure_one()
        data = {
            "form": {
                "date_start": fields.Datetime.to_string(self.date_start),
                "date_end": fields.Datetime.to_string(self.date_end),
                "check": self.check,
            }
        }
        return self.env.ref(report_xmlid).report_action(self, data=data)

    def print_rest_report(self):
        return self._print("hotel_restaurant.report_hotel_res_folio")

    def print_reserv_report(self):
        return self._print("hotel_restaurant.report_hotel_res_folio1")

    @api.constrains("date_start", "date_end")
    def check_date(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError(
                    self.env._("End date must be Greater than the Start date")
                )
