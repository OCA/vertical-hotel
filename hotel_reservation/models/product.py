from odoo import api, fields, models
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        """
        Custom search_fetch override:
          - When called with context["from_room"],
            restricts to available rooms for given dates.
        """
        context = self._context or {}
        if context.get("folio"):
            domain = domain.copy()
            checkin_date = context.get("checkin_date")
            checkout_date = context.get("checkout_date")

            if isinstance(checkin_date, str):
                checkin_date = fields.Datetime.from_string(checkin_date)
            if isinstance(checkout_date, str):
                checkout_date = fields.Datetime.from_string(checkout_date)

            if checkin_date and checkout_date:
                HotelRoom = self.env["hotel.reservation"].sudo()
                rooms = HotelRoom.search(
                    [
                        ("checkin", "<=", checkin_date),
                        ("state", "!=", "cancel"),
                        ("checkout", ">=", checkin_date),
                    ]
                )
                product_ids = rooms.mapped("reservation_line.reserve.product_id")
                domain = expression.AND([domain, [("id", "not in", product_ids.ids)]])

        return super().search_fetch(
            domain, field_names, offset=offset, limit=limit, order=order
        )
