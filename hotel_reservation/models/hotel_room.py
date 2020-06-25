from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt


class HotelRoom(models.Model):
    _inherit = "hotel.room"
    _description = "Hotel Room"

    room_reservation_line_ids = fields.One2many(
        "hotel.room.reservation.line", "room_id", string="Room Reserve Line"
    )

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        for room in self:
            for reserv_line in room.room_reservation_line_ids:
                if reserv_line.status == "confirm":
                    raise ValidationError(
                        _(
                            "User is not able to delete the \
                                            room after the room in %s state \
                                            in reservation"
                        )
                        % (reserv_line.status)
                    )
        return super(HotelRoom, self).unlink()

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
        now = datetime.now()
        curr_date = now.strftime(dt)
        for room in self.search([]):
            reserv_line_ids = [
                reservation_line.id
                for reservation_line in room.room_reservation_line_ids
            ]
            reserv_args = [
                ("id", "in", reserv_line_ids),
                ("check_in", "<=", curr_date),
                ("check_out", ">=", curr_date),
            ]
            reservation_line_ids = reservation_line_obj.search(reserv_args)
            rooms_ids = [room_line.id for room_line in room.room_line_ids]
            rom_args = [
                ("id", "in", rooms_ids),
                ("check_in", "<=", curr_date),
                ("check_out", ">=", curr_date),
            ]
            room_line_ids = folio_room_line_obj.search(rom_args)
            status = {"isroom": True, "color": 5}
            if reservation_line_ids.ids:
                status = {"isroom": False, "color": 2}
            room.write(status)
            if room_line_ids.ids:
                status = {"isroom": False, "color": 2}
            room.write(status)
            if reservation_line_ids.ids and room_line_ids.ids:
                raise ValidationError(
                    _("Please Check Rooms Status for %s.") % room.name
                )
        return True
