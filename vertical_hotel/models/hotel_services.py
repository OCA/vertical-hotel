# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import ClassVar

from odoo import api, fields, models

from .hotel_room import hierarchical_name_domain, is_hierarchical_search


class HotelServices(models.Model):
    _name = "hotel.services"
    _description = "Hotel Services and its charges"
    _inherits: ClassVar[dict] = {"product.product": "product_id"}

    product_id = fields.Many2one(
        "product.product",
        "Service_id",
        required=True,
        ondelete="cascade",
    )
    service_categ_id = fields.Many2one(
        "hotel.service.type",
        "Service Category",
        required=True,
        ondelete="restrict",
    )
    product_manager = fields.Many2one("res.users")

    @api.model_create_multi
    def create(self, vals_list):
        service_type_obj = self.env["hotel.service.type"]
        for vals in vals_list:
            if not vals.get("product_id"):
                # sold, never delivered: no delivery order on confirmation
                vals.setdefault("type", "service")
            if "service_categ_id" in vals:
                service_categ = service_type_obj.browse(vals.get("service_categ_id"))
                vals.update({"categ_id": service_categ.product_categ_id.id})
        return super().create(vals_list)

    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if "service_categ_id" in vals:
            service_categ_id = self.env["hotel.service.type"].browse(
                vals.get("service_categ_id")
            )
            vals.update({"categ_id": service_categ_id.product_categ_id.id})
        return super().write(vals)


class HotelServiceType(models.Model):
    _name = "hotel.service.type"
    _description = "Service Type"
    _inherits: ClassVar[dict] = {"product.category": "product_categ_id"}
    _rec_name = "name"

    service_id = fields.Many2one("hotel.service.type", "Service Category")
    child_ids = fields.One2many(
        "hotel.service.type", "service_id", "Service Child Categories"
    )
    product_categ_id = fields.Many2one(
        "product.category",
        "Product Category",
        required=True,
        copy=False,
        ondelete="restrict",
    )

    @api.model_create_multi
    def create(self, vals_list):
        service_type_obj = self.env["hotel.service.type"]
        for vals in vals_list:
            if "service_id" in vals:
                service_categ = service_type_obj.browse(vals.get("service_id"))
                vals.update({"parent_id": service_categ.product_categ_id.id})
        return super().create(vals_list)

    def write(self, vals):
        if "service_id" in vals:
            service_categ = self.env["hotel.service.type"].browse(
                vals.get("service_id")
            )
            vals.update({"parent_id": service_categ.product_categ_id.id})
        return super().write(vals)

    def _compute_display_name(self):
        def get_names(cat):
            """Return the list [cat.name, cat.service_id.name, ...]"""
            res = []
            while cat:
                if cat.name:
                    res.append(cat.name)
                cat = cat.service_id
            return res

        for cat in self:
            cat.display_name = " / ".join(reversed(get_names(cat))) or ""

    @api.model
    def _search_display_name(self, operator, value):
        if is_hierarchical_search(operator, value):
            return hierarchical_name_domain("service_id", operator, value)
        return super()._search_display_name(operator, value)
