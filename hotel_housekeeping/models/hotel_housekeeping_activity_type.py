# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class HotelHousekeepingActivityType(models.Model):
    _name = "hotel.housekeeping.activity.type"
    _description = "Activity Type"
    _rec_name = "name"

    name = fields.Char(required=True)
    activity_id = fields.Many2one("hotel.housekeeping.activity.type", "Activity Type")

    def _compute_display_name(self):
        def get_names(cat):
            """Return the list [cat.name, cat.activity_id.name, ...]"""
            res = []
            while cat:
                if cat.name:
                    res.append(cat.name)
                cat = cat.activity_id
            return res

        for cat in self:
            cat.display_name = " / ".join(reversed(get_names(cat))) or ""

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        if not domain:
            domain = []
        if name:
            # Be sure name_search is symetric to name_get
            category_names = name.split(" / ")
            parents = list(category_names)
            child = parents.pop()
            domain = [("name", operator, child)]
            if parents:
                names_ids = self.name_search(
                    " / ".join(parents),
                    domain=domain,
                    operator="ilike",
                    limit=limit,
                )
                category_ids = [name_id[0] for name_id in names_ids]
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    categories = self.search([("id", "not in", category_ids)])
                    domain = expression.OR(
                        [[("activity_id", "in", categories.ids)], domain]
                    )
                else:
                    domain = expression.AND(
                        [[("activity_id", "in", category_ids)], domain]
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
            categories = self._search(
                expression.AND([domain, domain]), limit=limit, order=order
            )
        else:
            categories = self._search(
                expression.AND([[("name", operator, name)], domain]),
                limit=limit,
                order=order,
            )

        return categories
