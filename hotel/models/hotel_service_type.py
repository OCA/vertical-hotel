# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression


class HotelServiceType(models.Model):
    _name = "hotel.service.type"
    _description = "Service Type"

    name = fields.Char("Service Name", size=64, required=True)
    service_id = fields.Many2one("hotel.service.type", "Service Category")
    child_ids = fields.One2many(
        "hotel.service.type", "service_id", "Child Categories"
    )

    @api.multi
    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.service_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.service_id
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
                        [[("service_id", "in", categories.ids)], domain]
                    )
                else:
                    domain = expression.AND(
                        [[("service_id", "in", category_ids)], domain]
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
