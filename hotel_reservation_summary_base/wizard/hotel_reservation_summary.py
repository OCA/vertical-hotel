# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Date


class RoomReservationSummary(models.AbstractModel):
    _name = "hotel.room.reservation.summary"
    _description = "Alternative Room reservation summary"
    _form_view = "implementation_module.set_in_implementation_model"

    name = fields.Char(compute="_compute_name")
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    room_summary = fields.Text(
        string="Room Summary", compute="_compute_room_summary"
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

    @api.model
    def _compute_headers(self, date_from, date_to):
        """
        :param date_from: datetime.date
        :param date_to: datetime.date
        :return:
        """
        nb_days = (date_to - date_from).days

        days = (date_from + timedelta(days=i) for i in range(nb_days))
        days = [day.strftime("%a %d %b") for day in days]
        headers = [_("Rooms")] + days
        return headers

    @api.multi
    @api.depends("date_from", "date_to")
    def _compute_room_summary(self, rooms=None):
        self.ensure_one()
        if rooms is None:
            rooms = self.env["hotel.room"].search([])

        if not rooms:
            raise ValidationError(_("No room defined in the hotel."))

        date_from = Date.from_string(self.date_from)
        date_to = Date.from_string(self.date_to)

        # align to previous monday
        date_from = date_from - timedelta(days=date_from.weekday())

        # align to next monday
        if date_to.weekday() != 0:
            date_to = date_to + timedelta(days=7 - date_to.weekday())

        week_start = date_from
        week_end = date_from + timedelta(days=7)

        room_summary = []
        while week_end <= date_to:
            week_data = {
                "headers": self._compute_headers(week_start, week_end),
                "rows": [
                    room.get_room_summary(week_start, week_end)
                    for room in rooms
                ],
            }
            room_summary.append(week_data)
            week_start += timedelta(days=7)
            week_end += timedelta(days=7)

        self.room_summary = str(room_summary)
        return room_summary
