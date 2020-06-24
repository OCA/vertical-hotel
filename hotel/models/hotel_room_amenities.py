# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression


class HotelRoomAmenitiesType(models.Model):
    _name = "hotel.room.amenities.type"
    _description = "amenities Type"

    name = fields.Char(required=True)
    amenity_id = fields.Many2one("hotel.room.amenities.type", "Category")
    child_ids = fields.One2many(
        "hotel.room.amenities.type", "amenity_id", "Child Categories"
    )

    @api.multi
    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.amenity_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.amenity_id
            return res

        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        if not args:
            args = []
        if name:
            # Be sure name_search is symetric to name_get
            category_names = name.split(" / ")
            parents = list(category_names)
            child = parents.pop()
            domain = [("name", operator, child)]
            if parents:
                names_ids = self.name_search(
                    " / ".join(parents),
                    args=args,
                    operator="ilike",
                    limit=limit,
                )
                category_ids = [name_id[0] for name_id in names_ids]
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    categories = self.search([("id", "not in", category_ids)])
                    domain = expression.OR(
                        [[("amenity_id", "in", categories.ids)], domain]
                    )
                else:
                    domain = expression.AND(
                        [[("amenity_id", "in", category_ids)], domain]
                    )
                for i in range(1, len(category_names)):
                    domain = [
                        [
                            (
                                "name",
                                operator,
                                " / ".join(category_names[-1 - i :]),
                            )
                        ],
                        domain,
                    ]
                    if operator in expression.NEGATIVE_TERM_OPERATORS:
                        domain = expression.AND(domain)
                    else:
                        domain = expression.OR(domain)
            categories = self.search(
                expression.AND([domain, args]), limit=limit
            )
        else:
            categories = self.search(args, limit=limit)
        return categories.name_get()


class HotelRoomAmenities(models.Model):
    _name = "hotel.room.amenities"
    _description = "Room amenities"

    product_id = fields.Many2one(
        "product.product",
        "Product Category",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    categ_id = fields.Many2one(
        "hotel.room.amenities.type", string="Amenities Category", required=True
    )
    product_manager = fields.Many2one("res.users", string="Product Manager")
