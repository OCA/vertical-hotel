# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# hotel_front_desk_dashboard reads these state keys with SQL: keep them.
HOUSEKEEPING_STATES = [
    ("inspect", "Inspect"),
    ("dirty", "Dirty"),
    ("clean", "Clean"),
    ("done", "Done"),
    ("cancel", "Cancelled"),
]
# The states a job may come from, per target state.
ALLOWED_TRANSITIONS = {
    "dirty": ("inspect", "dirty", "clean"),
    "clean": ("inspect", "dirty"),
    "done": ("clean",),
    "cancel": ("inspect", "dirty", "clean"),
    "inspect": ("cancel",),
}


class HotelHousekeeping(models.Model):
    _name = "hotel.housekeeping"
    _description = "Hotel Housekeeping"
    _rec_name = "room_id"
    _order = "current_date desc, id desc"

    current_date = fields.Date(
        "Today's Date",
        required=True,
        index=True,
        default=fields.Date.context_today,
    )
    clean_type = fields.Selection(
        [
            ("daily", "Daily"),
            ("checkin", "Check-In"),
            ("checkout", "Check-Out"),
        ],
        required=True,
        default="daily",
    )
    room_id = fields.Many2one(
        "hotel.room",
        "Room No",
        required=True,
        index=True,
    )
    activity_line_ids = fields.One2many(
        "hotel.housekeeping.activities",
        "housekeeping_id",
        "Activities",
        help="Detail of housekeeping activities",
    )
    inspector_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
    )
    inspect_date_time = fields.Datetime(
        help="When the inspector checked the cleaned room. "
        "Set automatically when the job is marked as done.",
    )
    quality = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("average", "Average"),
            ("bad", "Bad"),
            ("ok", "Ok"),
        ],
        help="Inspector inspect the room and mark "
        "as Excellent, Average, Bad, Good or Ok.",
    )
    state = fields.Selection(
        HOUSEKEEPING_STATES,
        required=True,
        readonly=True,
        default="inspect",
        group_expand=True,
    )

    @api.depends("room_id.name", "current_date")
    def _compute_display_name(self):
        for record in self:
            if record.room_id and record.current_date:
                record.display_name = (
                    f"{record.room_id.name} "
                    f"({fields.Date.to_string(record.current_date)})"
                )
            else:
                record.display_name = record.room_id.name or ""

    def _set_state(self, state, vals=None):
        """Move the jobs to ``state``, refusing transitions the workflow
        does not allow (the buttons hide them, server actions do not)."""
        wrong = self.filtered(lambda r: r.state not in ALLOWED_TRANSITIONS[state])
        if wrong:
            labels = dict(self._fields["state"]._description_selection(self.env))
            raise UserError(
                self.env._(
                    "%(jobs)s cannot be set to %(state)s.",
                    jobs=", ".join(wrong.mapped("display_name")),
                    state=labels[state],
                )
            )
        self.write(dict(vals or {}, state=state))

    def action_set_to_dirty(self):
        """
        This method is used to change the state
        to dirty of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self._set_state("dirty", {"quality": False})
        self.activity_line_ids.write({"is_clean": False, "is_dirty": True})

    def room_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self._set_state("cancel", {"quality": False})

    def room_done(self):
        """
        This method is used to change the state
        to done of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        missing = self.filtered(lambda r: not r.quality)
        if missing:
            raise ValidationError(
                self.env._(
                    "Please update quality of work for %(jobs)s!",
                    jobs=", ".join(missing.mapped("display_name")),
                )
            )
        self._set_state("done")
        self.filtered(lambda r: not r.inspect_date_time).write(
            {"inspect_date_time": fields.Datetime.now()}
        )

    def room_inspect(self):
        """
        This method is used to change the state
        to inspect of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self._set_state("inspect", {"quality": False})

    def room_clean(self):
        """
        This method is used to change the state
        to clean of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self._set_state("clean", {"quality": False})
        self.activity_line_ids.write({"is_clean": True, "is_dirty": False})

    @api.constrains("inspect_date_time")
    def check_end_date_time(self):
        self.activity_line_ids._check_inspect_after_cleaning()
