# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date, timedelta

from odoo import _, api, models
from odoo.fields import Date


class RoomReservationSummary(models.TransientModel):
    _name = "hotel.room.reservation.summary.week"
    _inherit = "hotel.room.reservation.summary"
    _form_view = (
        "hotel_reservation_summary_week"
        ".hotel_room_reservation_summary_week_form_view"
    )

    @api.multi
    @api.depends("date_from")
    def _compute_name(self):
        for summary in self:
            week_number = Date.from_string(summary.date_from).isocalendar()[1]
            summary.name = _("Week %s") % week_number

    @api.model
    def action_generate_summary(self):
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        next_monday = monday + timedelta(days=7)

        wizard = self.create({"date_from": monday, "date_to": next_monday})
        return wizard.get_summary_action()

    @api.multi
    def next_week_action(self):
        self.ensure_one()
        week_start = Date.from_string(self.date_from) + timedelta(days=7)
        next_week_start = Date.from_string(self.date_to) + timedelta(days=7)
        self.date_from = week_start
        self.date_to = next_week_start
        return self.get_summary_action()

    @api.multi
    def last_week_action(self):
        self.ensure_one()
        week_start = Date.from_string(self.date_from) - timedelta(days=7)
        next_week_start = Date.from_string(self.date_to) - timedelta(days=7)
        self.date_from = week_start
        self.date_to = next_week_start
        return self.get_summary_action()
