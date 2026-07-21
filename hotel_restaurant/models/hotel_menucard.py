# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Domain
from odoo.orm.domains import NEGATIVE_CONDITION_OPERATORS


class HotelMenucardType(models.Model):
    _name = "hotel.menucard.type"  # need to recheck for v15
    _description = "Food Item Type"

    name = fields.Char(required=True)
    child_ids = fields.One2many("hotel.menucard.type", "menu_id", "Child Categories")
    menu_id = fields.Many2one("hotel.menucard.type", "Food Item Type")
    # the compute walks up the menu_id chain, so the dependency is recursive
    display_name = fields.Char(compute="_compute_display_name", recursive=True)

    @api.depends("name", "menu_id.display_name")
    def _compute_display_name(self):
        def get_names(cat):
            """Return the list [cat.name, cat.menu_id.name, ...]"""
            res = []
            while cat:
                if cat.name:
                    res.append(cat.name)
                cat = cat.menu_id
            return res

        for cat in self:
            cat.display_name = " / ".join(reversed(get_names(cat))) or ""

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        domain = Domain(domain or Domain.TRUE)
        if not name:
            return self._search(
                Domain("name", operator, name) & domain, limit=limit, order=order
            )
        # Be sure name_search is symetric to _compute_display_name
        category_names = name.split(" / ")
        parents = list(category_names)
        child = parents.pop()
        name_domain = Domain("name", operator, child)
        if parents:
            names_ids = self.name_search(
                " / ".join(parents),
                domain=domain,
                operator="ilike",
                limit=limit,
            )
            category_ids = [name_id[0] for name_id in names_ids]
            if operator in NEGATIVE_CONDITION_OPERATORS:
                categories = self.search([("id", "not in", category_ids)])
                name_domain = Domain("menu_id", "in", categories.ids) | name_domain
            else:
                name_domain = Domain("menu_id", "in", category_ids) & name_domain
            for i in range(1, len(category_names)):
                parent_domain = Domain(
                    "name", operator, " / ".join(category_names[-1 - i :])
                )
                if operator in NEGATIVE_CONDITION_OPERATORS:
                    name_domain = parent_domain & name_domain
                else:
                    name_domain = parent_domain | name_domain
        return self._search(name_domain & domain, limit=limit, order=order)


class HotelMenucard(models.Model):
    _name = "hotel.menucard"
    _inherits = {"product.product": "product_id"}
    _description = "Hotel Menucard"

    product_id = fields.Many2one(
        "product.product",
        "Hotel Menucard",
        required=True,
        delegate=True,
        ondelete="cascade",
        index=True,
    )
    menu_card_categ_id = fields.Many2one("hotel.menucard.type", "Food Item Category")
    product_manager_id = fields.Many2one("res.users", "Product Manager")
