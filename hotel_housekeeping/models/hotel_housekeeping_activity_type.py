# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Domain


class HotelHousekeepingActivityType(models.Model):
    _name = "hotel.housekeeping.activity.type"
    _description = "Activity Type"
    _rec_name = "name"

    name = fields.Char(required=True)
    parent_id = fields.Many2one("hotel.housekeeping.activity.type", "Parent Category")
    # The display name walks up the whole parent chain, so it depends on itself
    display_name = fields.Char(recursive=True)

    @api.depends("name", "parent_id.display_name")
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
    def _search_display_name(self, operator, value):
        """Allow searching a category by its full path, e.g. "Parent / Child"."""
        if not isinstance(value, str) or " / " not in value:
            return super()._search_display_name(operator, value)
        if not operator.endswith("like") or operator.startswith("not"):
            return super()._search_display_name(operator, value)

        # Split the input name into hierarchy parts
        *parent_names, child_name = value.split(" / ")
        search_domain = Domain("name", operator, child_name)

        # Search all possible parent categories in one query
        parent_ids = self.search([("name", "in", parent_names)]).ids
        if parent_ids:
            search_domain &= Domain("parent_id", "in", parent_ids)

        return search_domain
