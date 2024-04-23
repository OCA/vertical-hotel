# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HotelHousekeeping(models.Model):
    _name = "hotel.housekeeping"
    _description = "Hotel Housekeeping"
    _rec_name = "room_id"

    current_date = fields.Date(
        "Today's Date",
        required=True,
        index=True,
        default=fields.Date.today,
    )
    clean_type = fields.Selection(
        [
            ("daily", "Daily"),
            ("checkin", "Check-In"),
            ("checkout", "Check-Out"),
        ],
        required=True,
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
        "Inspector",
        required=True,
    )
    inspect_date_time = fields.Datetime(
        required=True,
    )
    quality = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("average", "Average"),
            ("bad", "Bad"),
            ("ok", "Ok"),
        ],
        help="Inspector inspect the room and mark"
        "as Excellent, Average, Bad, Good or Ok. ",
    )
    state = fields.Selection(
        [
            ("inspect", "Inspect"),
            ("dirty", "Dirty"),
            ("clean", "Clean"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        required=True,
        readonly=True,
        default="inspect",
    )

    def action_set_to_dirty(self):
        """
        This method is used to change the state
        to dirty of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({"state": "dirty", "quality": False})
        self.activity_line_ids.write({"is_clean": False, "is_dirty": True})

    def room_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({"state": "cancel", "quality": False})

    def room_done(self):
        """
        This method is used to change the state
        to done of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        if not self.quality:
            raise ValidationError(_("Please update quality of work!"))
        self.write({"state": "done"})

    def room_inspect(self):
        """
        This method is used to change the state
        to inspect of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({"state": "inspect", "quality": False})

    def room_clean(self):
        """
        This method is used to change the state
        to clean of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({"state": "clean", "quality": False})
        self.activity_line_ids.write({"is_clean": True, "is_dirty": False})

    @api.constrains(
        "activity_line_ids", "activity_line_ids.clean_end_time", "inspect_date_time"
    )
    def check_end_date_time(self):
        for record in self:
            for rec in record.activity_line_ids:
                if (
                    record.inspect_date_time
                    and record.inspect_date_time <= rec.clean_end_time
                ):
                    raise ValidationError(
                        "Inspect Date Time must be Greter, then Clean end time"
                    )
