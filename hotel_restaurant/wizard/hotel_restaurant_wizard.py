# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WizardHotelRestaurant(models.TransientModel):
    _name = "wizard.hotel.restaurant"
    _description = "wizard.hotel.restaurant"

    date_start = fields.Datetime("Start Date", required=True)
    date_end = fields.Datetime("End Date", required=True)

    def print_report(self):
        data = {
            "ids": self.ids,
            "model": "hotel.restaurant.reservation",
            "form": self.read(["date_start", "date_end"])[0],
        }
        return self.env.ref("hotel_restaurant.report_hotel_table_res").report_action(
            self, data=data
        )

    @api.constrains("date_start", "date_end")
    def check_date(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError(_("End date must be Greater than the Start date"))


class FolioRestReservation(models.TransientModel):
    _name = "folio.rest.reservation"
    _description = "folio.rest.reservation"
    _rec_name = "date_start"

    date_start = fields.Datetime("Start Date")
    date_end = fields.Datetime("End Date")
    check = fields.Boolean("With Details")

    def print_rest_report(self):
        data = {
            "ids": self.ids,
            "model": "hotel.folio",
            "form": self.read(["date_start", "date_end", "check"])[0],
        }
        return self.env.ref("hotel_restaurant.report_hotel_res_folio").report_action(
            self, data=data
        )

    def print_reserv_report(self):
        data = {
            "ids": self.ids,
            "model": "hotel.folio",
            "form": self.read(["date_start", "date_end", "check"])[0],
        }
        return self.env.ref("hotel_restaurant.report_hotel_res_folio1").report_action(
            self, data=data
        )

    @api.constrains("date_start", "date_end")
    def check_date(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError(_("End date must be Greater than the Start date"))
