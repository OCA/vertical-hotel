# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date, timedelta

from odoo import api, models


class RoomReservationSummary(models.TransientModel):
    _name = "hotel.room.reservation.summary.range"
    _inherit = "hotel.room.reservation.summary"
    _form_view = (
        "hotel_reservation_summary_range"
        ".hotel_room_reservation_summary_range_form_view"
    )

    @api.model
    def action_generate_summary(self):
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        next_monday = monday + timedelta(days=7)

        wizard = self.create({"date_from": monday, "date_to": next_monday})
        return wizard.get_summary_action()
