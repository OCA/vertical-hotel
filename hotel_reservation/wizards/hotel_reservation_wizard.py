# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HotelReservationWizard(models.TransientModel):
    _name = "hotel.reservation.wizard"
    _description = "Allow to generate a reservation"

    date_start = fields.Datetime(
        string="Start Date",
        required=True,
    )
    date_end = fields.Datetime(
        string="End Date",
        required=True,
    )

    def report_reservation_detail(self):
        data = {
            "ids": self.ids,
            "model": "hotel.reservation",
            "form": self.read(["date_start", "date_end"])[0],
        }
        return self.env.ref("hotel_reservation.hotel_roomres_details").report_action(
            self, data=data
        )

    def report_checkin_detail(self):
        data = {
            "ids": self.ids,
            "model": "hotel.reservation",
            "form": self.read(["date_start", "date_end"])[0],
        }
        return self.env.ref("hotel_reservation.hotel_checkin_details").report_action(
            self, data=data
        )

    def report_checkout_detail(self):
        data = {
            "ids": self.ids,
            "model": "hotel.reservation",
            "form": self.read(["date_start", "date_end"])[0],
        }
        return self.env.ref("hotel_reservation.hotel_checkout_details").report_action(
            self, data=data
        )

    def report_maxroom_detail(self):
        data = {
            "ids": self.ids,
            "model": "hotel.reservation",
            "form": self.read(["date_start", "date_end"])[0],
        }
        return self.env.ref("hotel_reservation.hotel_maxroom_details").report_action(
            self, data=data
        )
