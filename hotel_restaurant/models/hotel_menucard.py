# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import ClassVar

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.vertical_hotel.models.hotel_room import (
    hierarchical_name_domain,
    is_hierarchical_search,
)


class HotelMenucardType(models.Model):
    _name = "hotel.menucard.type"
    _description = "Food Item Type"

    name = fields.Char(required=True)
    child_ids = fields.One2many("hotel.menucard.type", "menu_id", "Child Categories")
    menu_id = fields.Many2one("hotel.menucard.type", "Food Item Type", index=True)
    # the compute walks up the menu_id chain, so the dependency is recursive
    display_name = fields.Char(compute="_compute_display_name", recursive=True)

    @api.depends("name", "menu_id.display_name")
    def _compute_display_name(self):
        def get_names(cat):
            """Return the list [cat.name, cat.menu_id.name, ...]"""
            res = []
            seen = set()
            while cat and cat.id not in seen:
                seen.add(cat.id)
                if cat.name:
                    res.append(cat.name)
                cat = cat.menu_id
            return res

        for cat in self:
            cat.display_name = " / ".join(reversed(get_names(cat))) or ""

    @api.constrains("menu_id")
    def _check_menu_id(self):
        if self._has_cycle("menu_id"):
            raise ValidationError(
                self.env._("You cannot create recursive food item types.")
            )

    @api.model
    def _search_display_name(self, operator, value):
        """Allow searching a category by its full path, e.g. "Parent / Child"."""
        if is_hierarchical_search(operator, value):
            return hierarchical_name_domain("menu_id", operator, value)
        return super()._search_display_name(operator, value)


class HotelMenucard(models.Model):
    _name = "hotel.menucard"
    _inherits: ClassVar[dict] = {"product.product": "product_id"}
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
    product_manager_id = fields.Many2one("res.users")
