# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HotelActivity(models.Model):
    _name = 'hotel.activity'
    _description = 'Housekeeping Activity'

    h_id = fields.Many2one(
        'product.product',
        'Product',
        required=True,
        delegate=True,
        ondelete='cascade',
        index=True
    )
    categ_id = fields.Many2one(
        'hotel.housekeeping.activity.type',
        string='Category'
    )
