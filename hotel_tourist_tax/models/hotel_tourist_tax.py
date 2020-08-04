# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HotelTouristTax(models.Model):
    _name = "hotel.tourist.tax"
    _description = "Hotel Tourist Tax"

    hotel_service_id = fields.Many2one(
        comodel_name="hotel.services",
        string="Service",
        required=True,
        ondelete="cascade",
        delegate=True,
    )

    auto_apply = fields.Boolean(
        sting="Apply Automatically", help="Apply Automatically", default=True
    )
    amount = fields.Float(string="Amount")
    per_night = fields.Boolean(sting="Per Night", default=True)
    per_person = fields.Boolean(sting="Per Person", default=True)
    count_adults = fields.Boolean(sting="Count Adults", default=True)
    count_children = fields.Boolean(sting="Count Children", default=False)

    @api.model
    def create(self, vals):
        cat_id = self.env.ref(
            "hotel_tourist_tax.hotel_service_type_tourist_tax"
        )
        res = super(
            HotelTouristTax,
            self.with_context(my_service_category_id=cat_id.id),
        ).create(vals)
        return res
