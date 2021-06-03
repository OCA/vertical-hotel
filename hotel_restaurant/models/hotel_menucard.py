from odoo import api, fields, models
from odoo.osv import expression


class HotelMenucardType(models.Model):

    _name = "hotel.menucard.type"  # need to recheck for v15
    _description = "Food Item Type"

    name = fields.Char("Name", required=True)
    menu_id = fields.Many2one("hotel.menucard.type", "Food Item Type")
    child_ids = fields.One2many("hotel.menucard.type", "menu_id", "Child Categories")

    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.menu_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.menu_id
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
                        [[("menu_id", "in", categories.ids)], domain]
                    )
                else:
                    domain = expression.AND([[("menu_id", "in", category_ids)], domain])
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
            categories = self.search(expression.AND([domain, args]), limit=limit)
        else:
            categories = self.search(args, limit=limit)
        return categories.name_get()


class HotelMenucard(models.Model):

    _name = "hotel.menucard"
    _description = "Hotel Menucard"

    product_id = fields.Many2one(
        "product.product",
        "Hotel Menucard",
        required=True,
        delegate=True,
        ondelete="cascade",
        index=True,
    )
    categ_id = fields.Many2one(
        "hotel.menucard.type", "Food Item Category", required=True
    )
    product_manager_id = fields.Many2one("res.users", "Product Manager")
