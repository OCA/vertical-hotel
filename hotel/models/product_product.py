# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    isroom = fields.Boolean("Is Room")
    iscategid = fields.Boolean("Is Categ")
    isservice = fields.Boolean("Is Service")
