# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date

from odoo import api, models
from odoo.fields import Date


class RoomReservationSummary(models.TransientModel):
    _name = "hotel.room.reservation.summary.month"
    _inherit = "hotel.room.reservation.summary"
    _form_view = (
        "hotel_reservation_summary_month"
        ".hotel_room_reservation_summary_month_form_view"
    )

    @api.multi
    @api.depends("date_from")
    def _compute_name(self):
        for summary in self:
            month = Date.from_string(summary.date_from).strftime("%B")
            summary.name = month

    @api.model
    def action_generate_summary(self):
        first = date.today().replace(day=1)
        next_month = (first.month + 1) % 12
        next_first = first.replace(month=next_month)
        wizard = self.create(
            {
                "date_from": Date.to_string(first),
                "date_to": Date.to_string(next_first),
            }
        )
        return wizard.get_summary_action()

    @api.multi
    def next_month_action(self):
        self.ensure_one()
        date_from = Date.from_string(self.date_from)
        date_from = date_from.replace(month=(date_from.month + 1) % 12)
        date_to = date_from.replace(month=(date_from.month + 1) % 12)

        self.date_from = date_from
        self.date_to = date_to
        return self.get_summary_action()

    @api.multi
    def previous_month_action(self):
        self.ensure_one()
        date_from = Date.from_string(self.date_from)
        self.date_from = date_from.replace(month=(date_from.month - 1) % 12)
        self.date_to = date_from
        return self.get_summary_action()
