# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt


class HotelRoom(models.Model):
    _inherit = "hotel.room"
    _description = "Hotel Room"

    room_reservation_line_ids = fields.One2many(
        comodel_name="hotel.room.reservation.line",
        inverse_name="room_id",
        string="Room Reserve Line",
    )

    def unlink(self):
        for room in self:
            for reserv_line in room.room_reservation_line_ids:
                if reserv_line.status == "confirm":
                    raise ValidationError(
                        _(
                            """User is not able to delete the """
                            """room after the room in %s state """
                            """in reservation"""
                        )
                        % (reserv_line.status)
                    )
        return super().unlink()

    @api.model
    def cron_room_line(self):
        """
        This method is for scheduler
        every 1min scheduler will call this method and check Status of
        room is occupied or available
        --------------------------------------------------------------
        @param self: The object pointer
        @return: update status of hotel room reservation line
        """
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        folio_room_line_obj = self.env["folio.room.line"]
        curr_date = fields.Datetime.now().strftime(dt)
        for room in self.search([]):
            reserv_line_ids = room.room_reservation_line_ids.ids
            reservation_line_ids = reservation_line_obj.search(
                [
                    ("id", "in", reserv_line_ids),
                    ("check_in", "<=", curr_date),
                    ("check_out", ">=", curr_date),
                ]
            )
            rooms_ids = room.room_line_ids.ids
            room_line_ids = folio_room_line_obj.search(
                [
                    ("id", "in", rooms_ids),
                    ("check_in", "<=", curr_date),
                    ("check_out", ">=", curr_date),
                ]
            )
            status = {"isroom": True, "color": 5}
            if reservation_line_ids:
                status = {"isroom": False, "color": 2}
            room.write(status)
            if room_line_ids:
                status = {"isroom": False, "color": 2}
            room.write(status)
            if reservation_line_ids and room_line_ids:
                raise ValidationError(
                    _(
                        "Please Check Rooms Status for %(room_name)s.",
                        room_name=room.name,
                    )
                )
        return True
