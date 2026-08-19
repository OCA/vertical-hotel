# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Domain


class ProductProduct(models.Model):
    _inherit = "product.product"

    isroom = fields.Boolean("Is Room")
    iscategid = fields.Boolean("Is Categ")
    isservice = fields.Boolean("Is Service")

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        """
        Custom search_fetch override:
          - When called with context["from_room"],
            restricts to available rooms for given dates.
        """
        context = self.env.context or {}

        if context.get("from_room"):
            checkin_date = context.get("checkin_date")
            checkout_date = context.get("checkout_date")

            if isinstance(checkin_date, str):
                checkin_date = fields.Datetime.from_string(checkin_date)
            if isinstance(checkout_date, str):
                checkout_date = fields.Datetime.from_string(checkout_date)

            if checkin_date and checkout_date:
                HotelRoom = self.env["hotel.room"].sudo()
                avail_prod_ids = []
                # pylint: disable=no-search-all
                rooms = HotelRoom.search([])

                for room in rooms:
                    assigned = False
                    for rm_line in room.room_line_ids.filtered(
                        lambda line: line.status != "cancel"
                    ):
                        if (
                            (checkin_date <= rm_line.check_in <= checkout_date)
                            or (checkin_date <= rm_line.check_out <= checkout_date)
                            or (rm_line.check_in <= checkin_date <= rm_line.check_out)
                            or (rm_line.check_in <= checkout_date <= rm_line.check_out)
                        ):
                            assigned = True
                            break
                    if not assigned:
                        avail_prod_ids.append(room.product_id.id)

                domain = Domain.AND([domain, [("id", "in", avail_prod_ids)]])

        return super().search_fetch(
            domain, field_names, offset=offset, limit=limit, order=order
        )
