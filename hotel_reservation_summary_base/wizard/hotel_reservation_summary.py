# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import date, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Date


class RoomReservationSummary(models.AbstractModel):
    _name = "hotel.room.reservation.summary"
    _description = "Alternative Room reservation summary"
    _form_view = "implementation_module.set_in_implementation_model"  # todo doc

    name = fields.Char(compute="_compute_name")
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    summary_header = fields.Text(
        string="Summary Header", compute="_compute_summary_data"
    )
    room_summary = fields.Text(
        string="Room Summary", compute="_compute_summary_data"
    )

    @api.model
    def action_generate_summary(self):
        raise NotImplementedError

    @api.multi
    def get_summary_action(self):
        self.ensure_one()
        view = self.env.ref(self._form_view)

        action = {
            "name": "Summary Action",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_model": self._name,
            "view_id": view.id,
            "target": "current",
            "res_id": self.id,
            "context": self.env.context,
        }
        return action

    @api.multi
    @api.depends("date_from", "date_to")
    def _compute_name(self):
        for summary in self:
            summary.name = "{} - {}".format(self.date_from, self.date_to)

    @api.multi
    def _compute_headers(self):
        self.ensure_one()
        date_from = Date.from_string(self.date_from)
        date_to = Date.from_string(self.date_to)
        nb_days = (date_to - date_from).days

        days = (date_from + timedelta(days=i) for i in range(nb_days))
        days = [day.strftime("%a %d %b") for day in days]
        headers = [{"header": [_("Rooms")] + days}]
        return headers

    @api.multi
    def _compute_room_summary(self, rooms=None):
        self.ensure_one()
        if not rooms:
            rooms = self.env["hotel.room"].search([])

        if not rooms:
            raise ValidationError(_("No room defined in the hotel."))

        rooms_summary = [
            room.get_room_summary(self.date_from, self.date_to)
            for room in rooms
        ]

        return rooms_summary

    @api.multi
    @api.depends("date_from", "date_to")
    def _compute_summary_data(self):
        self.ensure_one()
        # todo only send one data dictionary?
        self.summary_header = str(self._compute_headers())
        self.room_summary = str(self._compute_room_summary())
