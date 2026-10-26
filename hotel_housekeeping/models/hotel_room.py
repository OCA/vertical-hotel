# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# Room housekeeping status for the state of its latest housekeeping job.
ROOM_STATUS_BY_JOB_STATE = {
    "inspect": "needs_cleaning",
    "dirty": "needs_cleaning",
    "clean": "to_inspect",
    "done": "ready",
}


class HotelRoom(models.Model):
    _inherit = "hotel.room"

    housekeeping_ids = fields.One2many(
        "hotel.housekeeping", "room_id", string="Housekeeping Jobs"
    )
    housekeeping_count = fields.Integer(compute="_compute_housekeeping_count")
    housekeeping_state = fields.Selection(
        [
            ("needs_cleaning", "Needs Cleaning"),
            ("to_inspect", "To Inspect"),
            ("ready", "Ready"),
        ],
        compute="_compute_housekeeping_state",
        store=True,
        help="Status of the latest housekeeping job of the room "
        "(cancelled jobs are ignored).",
    )

    @api.depends("housekeeping_ids.state", "housekeeping_ids.current_date")
    def _compute_housekeeping_state(self):
        for room in self:
            jobs = room.housekeeping_ids.filtered(lambda job: job.state != "cancel")
            # latest job first, like hotel_front_desk_dashboard does
            latest = jobs.sorted(
                lambda job: (job.current_date, job.id or 0), reverse=True
            )[:1]
            room.housekeeping_state = ROOM_STATUS_BY_JOB_STATE.get(latest.state)

    def _compute_housekeeping_count(self):
        counts = dict(
            self.env["hotel.housekeeping"]._read_group(
                [("room_id", "in", self.ids)], ["room_id"], ["__count"]
            )
        )
        for room in self:
            room.housekeeping_count = counts.get(room, 0)

    def action_view_housekeeping(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "hotel_housekeeping.open_hotel_housekeeping_form_tree"
        )
        action["domain"] = [("room_id", "=", self.id)]
        action["context"] = {"default_room_id": self.id}
        return action
