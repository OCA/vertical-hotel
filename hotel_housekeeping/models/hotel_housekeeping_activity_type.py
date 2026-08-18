# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class HotelHousekeepingActivityType(models.Model):
    _name = "hotel.housekeeping.activity.type"
    _description = "Activity Type"
    _rec_name = "name"

    name = fields.Char(required=True)
    parent_id = fields.Many2one("hotel.housekeeping.activity.type", "Parent Category")

    def _compute_display_name(self):
        def get_names(cat):
            """Return the list [cat.name, cat.parent_id.name, ...]"""
            res = []
            while cat:
                if cat.name:
                    res.append(cat.name)
                cat = cat.parent_id
            return res

        for cat in self:
            cat.display_name = " / ".join(reversed(get_names(cat))) or ""

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        domain = domain or []
        if not name:
            return self._search(domain, limit=limit, order=order)
        # Split the input name into hierarchy parts
        name_parts = name.split(" / ")
        child_name = name_parts[-1]
        parent_names = name_parts[:-1]

        # Base domain for the child category
        search_domain = expression.AND([domain, [("name", operator, child_name)]])

        if parent_names:
            # Search all possible parent categories in one query
            parent_ids = self.search([("name", "in", parent_names)]).ids
            if parent_ids:
                search_domain = expression.AND(
                    [search_domain, [("parent_id", "in", parent_ids)]]
                )

        # Perform final search
        category_ids = self._search(search_domain, limit=limit, order=order)
        return category_ids
