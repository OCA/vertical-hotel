# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HotelHousekeepingActivities(models.Model):
    _name = "hotel.housekeeping.activities"
    _description = "Housekeeping Activities"

    housekeeping_id = fields.Many2one("hotel.housekeeping", "Reservation")
    today_date = fields.Date()
    activity_id = fields.Many2one("hotel.activity", "Housekeeping Activity")
    housekeeper_id = fields.Many2one("res.users", "Housekeeper", required=True)
    clean_start_time = fields.Datetime(required=True)
    clean_end_time = fields.Datetime(required=True)
    is_dirty = fields.Boolean(
        "Dirty",
        help="Checked if the housekeeping activityresults as Dirty.",
    )
    is_clean = fields.Boolean(
        "Clean",
        help="Checked if the housekeepingactivity results as Clean.",
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

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        context = self.env.context
        if context.get("today_date", False):
            res.update({"today_date": context.get("today_date")})
        return res
