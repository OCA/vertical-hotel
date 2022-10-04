# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HotelActivity(models.Model):

    _name = "hotel.activity"
    _description = "Housekeeping Activity"

    product_id = fields.Many2one(
        "product.product",
        "Hotel Activity",
        required=True,
        delegate=True,
        ondelete="cascade",
        index=True,
    )
    categ_id = fields.Many2one("hotel.housekeeping.activity.type", "Category")
