# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HotelActivity(models.Model):
    _name = "hotel.activity"
    _description = "Housekeeping Activity"

    name = fields.Char("Name")
    categ_id = fields.Many2one("hotel.housekeeping.activity.type", "Category")
