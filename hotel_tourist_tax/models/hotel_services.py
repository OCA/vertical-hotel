# See LICENSE file for full copyright and licensing details.

from odoo import api, models


class HotelServices(models.Model):
    _inherit = "hotel.services"

    @api.model
    def create(self, vals):
        vals["categ_id"] = self.env.context.get("my_service_category_id")
        res = super().create(vals)
        return res
