# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    housekeeping_note = fields.Char(string="Housekeeping Note", required=False)
