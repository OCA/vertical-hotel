# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HotelReservationWizard(models.TransientModel):
    _name = "hotel.reservation.wizard"
    _description = "Allow to generate a reservation"

    date_start = fields.Datetime("Start Date", required=True)
    date_end = fields.Datetime("End Date", required=True)

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

    @api.constrains("date_start", "date_end")
    def check_date(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError(_("End date must be Greater than the Start date"))


class MakeFolioWizard(models.TransientModel):
    _name = "wizard.make.folio"
    _description = "Allow to generate the folio"

    grouped = fields.Boolean("Group the Folios")

    def make_folios(self):
        reservation_obj = self.env["hotel.reservation"]
        newinv = [
            order.id
            for order in reservation_obj.browse(
                self.env.context.get("active_ids", [])
            ).mapped("folio_id")
        ]
        return {
            "domain": "[('id','in', [" + ",".join(map(str, newinv)) + "])]",
            "name": "Folios",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "hotel.folio",
            "view_id": False,
            "type": "ir.actions.act_window",
        }
