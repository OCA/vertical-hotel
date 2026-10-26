# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HotelHousekeepingActivities(models.Model):
    _name = "hotel.housekeeping.activities"
    _description = "Housekeeping Activities"

    housekeeping_id = fields.Many2one(
        "hotel.housekeeping", index=True, ondelete="cascade"
    )
    today_date = fields.Date(default=fields.Date.context_today)
    activity_id = fields.Many2one("hotel.activity", "Housekeeping Activity")
    housekeeper_id = fields.Many2one("res.users", required=True)
    clean_start_time = fields.Datetime(required=True)
    clean_end_time = fields.Datetime(required=True)
    is_dirty = fields.Boolean(
        "Dirty",
        help="Checked if the housekeeping activity results as Dirty.",
    )
    is_clean = fields.Boolean(
        "Clean",
        help="Checked if the housekeeping activity results as Clean.",
    )

    @api.constrains("clean_start_time", "clean_end_time")
    def _check_clean_start_time(self):
        """
        This method is used to validate the clean_start_time and
        clean_end_time.
        ---------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        for activity in self:
            if activity.clean_start_time >= activity.clean_end_time:
                raise ValidationError(
                    self.env._("Start Time Should be less than the End Time!")
                )

    @api.constrains("clean_end_time", "housekeeping_id")
    def _check_inspect_after_cleaning(self):
        """The inspector checks the room once the cleaning is finished."""
        for activity in self:
            inspect_date_time = activity.housekeeping_id.inspect_date_time
            if inspect_date_time and activity.clean_end_time > inspect_date_time:
                raise ValidationError(
                    self.env._("Inspect Date Time must be greater than Clean end time")
                )
