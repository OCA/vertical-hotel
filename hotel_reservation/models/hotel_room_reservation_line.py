from odoo import fields, models


class HotelRoomReservationLine(models.Model):
    _name = "hotel.room.reservation.line"
    _description = "Hotel Room Reservation"
    _rec_name = "room_id"

    room_id = fields.Many2one("hotel.room", string="Room id")
    check_in = fields.Datetime("Check In Date", required=True)
    check_out = fields.Datetime("Check Out Date", required=True)
    state = fields.Selection(
        [("assigned", "Assigned"), ("unassigned", "Unassigned")], "Room Status"
    )
    reservation_id = fields.Many2one("hotel.reservation", string="Reservation")
    status = fields.Selection(string="state", related="reservation_id.state")
