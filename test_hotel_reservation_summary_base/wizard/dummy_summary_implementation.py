# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models


class RoomReservationSummaryTest(models.TransientModel):
    _name = "hotel.room.reservation.summary.test"
    _inherit = "hotel.room.reservation.summary"
