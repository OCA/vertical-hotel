# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Domain


class HotelServices(models.Model):
    _name = "hotel.services"
    _description = "Hotel Services and its charges"
    _inherits = {"product.product": "product_id"}

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
    _inherits = {"product.category": "product_categ_id"}
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
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        domain = domain or []
        if name:
            # Be sure name_search is symetric to name_get
            category_names = name.split(" / ")
            parents = list(category_names)
            child = parents.pop()
            domain = Domain.AND([domain, [("name", operator, child)]])
            if parents:
                category_ids = self.name_search(
                    " / ".join(parents),
                    domain=domain,
                    operator="ilike",
                    limit=limit,
                )
                if operator in Domain.NEGATIVE_TERM_OPERATORS:
                    categories = self.search([("id", "not in", category_ids)])
                    domain = Domain.OR(
                        [[("service_id", "not in", categories.ids)], domain]
                    )
                else:
                    domain = Domain.AND([[("service_id", "in", category_ids)], domain])
                for i in range(1, len(category_names)):
                    new_domain = [
                        (
                            "name",
                            operator,
                            " / ".join(category_names[-1 - i :]),
                        )
                    ]
                    if operator in Domain.NEGATIVE_TERM_OPERATORS:
                        domain = Domain.AND([domain, new_domain])
                    else:
                        domain = Domain.OR([domain, new_domain])

        return self._search(domain, limit=limit, order=order)
