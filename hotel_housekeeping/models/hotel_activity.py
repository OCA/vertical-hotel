# Copyright (C) 2023-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "name" in vals:
                existing_activity = self.env["hotel.activity"].search(
                    [("name", "ilike", vals["name"])], limit=1
                )
                if existing_activity:
                    raise ValidationError(
                        _(
                            "A activity with the name '%s' already exists."
                            "Please choose a different activity."
                        )
                        % vals["name"]
                    )
            return super(HotelActivity, self).create(vals)
