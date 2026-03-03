# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class HotelRoomReservationLine(models.Model):
    _name = "hotel.room.reservation.line"
    _description = "Hotel Room Reservation"
    _rec_name = "room_id"

    room_id = fields.Many2one(
        comodel_name="hotel.room",
    )
    check_in = fields.Datetime(
        string="Check In Date",
        required=True,
    )
    check_out = fields.Datetime(
        string="Check Out Date",
        required=True,
    )
    state = fields.Selection(
        selection=[
            ("assigned", "Assigned"),
            ("unassigned", "Unassigned"),
        ],
        string="Room Status",
    )
    reservation_id = fields.Many2one(
        comodel_name="hotel.reservation",
    )
    status = fields.Selection(
        string="state",
        related="reservation_id.state",
    )
