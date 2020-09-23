# See LICENSE file for full copyright and licensing details.

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
