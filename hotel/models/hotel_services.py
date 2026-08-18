# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class HotelServices(models.Model):
    _name = "hotel.services"
    _description = "Hotel Services and its charges"

    product_id = fields.Many2one(
        "product.product",
        "Service_id",
        required=True,
        ondelete="cascade",
        delegate=True,
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
        service_type_ids = [
            v.get("service_categ_id") for v in vals_list if v.get("service_categ_id")
        ]
        if service_type_ids:
            service_types = self.env["hotel.service.type"].browse(service_type_ids)
            type_to_categ = {
                t.id: t.product_categ_id.id for t in service_types if t.product_categ_id
            }
            for vals in vals_list:
                service_categ_id = vals.get("service_categ_id")
                if service_categ_id and service_categ_id in type_to_categ:
                    vals["categ_id"] = type_to_categ[service_categ_id]
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
    _rec_name = "name"

    service_id = fields.Many2one("hotel.service.type", "Service Category")
    child_ids = fields.One2many(
        "hotel.service.type", "service_id", "Service Child Categories"
    )
    product_categ_id = fields.Many2one(
        "product.category",
        "Product Category",
        delegate=True,
        required=True,
        copy=False,
        ondelete="restrict",
    )

    @api.model_create_multi
    def create(self, vals_list):
        service_ids = [v.get("service_id") for v in vals_list if v.get("service_id")]
        if service_ids:
            services = self.browse(service_ids)
            service_to_parent = {
                s.id: s.product_categ_id.id for s in services if s.product_categ_id
            }
            for vals in vals_list:
                service_id = vals.get("service_id")
                if service_id and service_id in service_to_parent:
                    vals["parent_id"] = service_to_parent[service_id]
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
