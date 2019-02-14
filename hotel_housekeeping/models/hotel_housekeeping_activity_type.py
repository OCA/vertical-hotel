# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression


class HotelHousekeepingActivityType(models.Model):

    _name = 'hotel.housekeeping.activity.type'
    _description = 'Activity Type'

    name = fields.Char('Name', required=True)
    activity_id = fields.Many2one('hotel.housekeeping.activity.type',
                                  'Activity Type')

    @api.multi
    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.activity_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.activity_id
            return res
        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            # Be sure name_search is symmetric to name_get
            category_names = name.split(' / ')
            parents = list(category_names)
            child = parents.pop()
            domain = [('name', operator, child)]
            if parents:
                names_ids = self.name_search(' / '.join(parents), args=args,
                                             operator='ilike', limit=limit)
                category_ids = [name_id[0] for name_id in names_ids]
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    categories = self.search([('id', 'not in', category_ids)])
                    domain = expression.OR([[('activity_id', 'in',
                                              categories.ids)], domain])
                else:
                    domain = expression.AND([[('activity_id', 'in',
                                               category_ids)], domain])
                for num in range(1, len(category_names)):
                    domain = [[('name', operator, ' / '.
                                join(category_names[-1 - num:]))], domain]
                    if operator in expression.NEGATIVE_TERM_OPERATORS:
                        domain = expression.AND(domain)
                    else:
                        domain = expression.OR(domain)
            categories = self.search(expression.AND([domain, args]),
                                     limit=limit)
        else:
            categories = self.search(args, limit=limit)
        return categories.name_get()
