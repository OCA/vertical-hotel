# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HotelServices(models.Model):
    _name = "hotel.services"
    _description = "Hotel Services and its charges"

    product_id = fields.Many2one(
        "product.product",
        "Service_id",
        required=True,
        ondelete="cascade",
        delegate=True,
    )
    categ_id = fields.Many2one(
        "hotel.service.type", string="Service Category", required=True
    )
    product_manager = fields.Many2one("res.users", string="Product Manager")
