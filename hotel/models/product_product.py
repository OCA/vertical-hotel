# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class ProductProduct(models.Model):

    _inherit = "product.product"

    isroom = fields.Boolean("Is Room")
    iscategid = fields.Boolean("Is Categ")
    isservice = fields.Boolean("Is Service")

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        args = args or []
        context = self._context or {}
        checkin_date = context.get("checkin_date")
        checkout_date = context.get("checkout_date")
        if isinstance(checkin_date, str):
            checkin_date = fields.datetime.strptime(
                context.get("checkin_date"), tools.DEFAULT_SERVER_DATETIME_FORMAT
            )
        if isinstance(checkout_date, str):
            checkout_date = fields.datetime.strptime(
                context.get("checkout_date"), tools.DEFAULT_SERVER_DATETIME_FORMAT
            )
        if checkin_date and checkout_date:
            hotel_room_obj = self.env["hotel.room"]
            avail_prod_ids = []
            for room in hotel_room_obj.search([]):
                assigned = False
                for rm_line in room.room_line_ids:
                    if rm_line.status != "cancel":
                        if (checkin_date <= rm_line.check_in <= checkout_date) or (
                            checkin_date <= rm_line.check_out <= checkout_date
                        ):
                            assigned = True
                        elif (
                            rm_line.check_in <= checkin_date <= rm_line.check_out
                        ) or (rm_line.check_in <= checkout_date <= rm_line.check_out):
                            assigned = True
                if not assigned:
                    avail_prod_ids.append(room.product_id.id)
            args.append(("id", "in", avail_prod_ids))
        return super(ProductProduct, self)._search(
            args, offset, limit, order, count=count, access_rights_uid=access_rights_uid
        )
