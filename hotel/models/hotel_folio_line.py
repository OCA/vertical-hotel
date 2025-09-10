# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class HotelFolioLine(models.Model):
    _name = "hotel.folio.line"
    _description = "Hotel Folio Line"

    order_line_id = fields.Many2one(
        "sale.order.line",
        "Order Line",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    folio_id = fields.Many2one("hotel.folio", "Folio", ondelete="cascade")
    checkin_date = fields.Datetime("Check In", required=True)
    checkout_date = fields.Datetime("Check Out", required=True)
    is_reserved = fields.Boolean(help="True when folio line created from Reservation")

    def _update_folio_line(self):
        """
        Sync folio room lines with hotel rooms.
        Works with:
          - hotel.folio   → updates all its room_line_ids
          - hotel.folio.line → updates only given lines
        """
        FolioRoomLine = self.env["folio.room.line"]
        hotel_room_obj = self.env["hotel.room"]

        product_ids = self.mapped("product_id").ids
        rooms = hotel_room_obj.search([("product_id", "in", product_ids)])
        room_by_product = {room.product_id.id: room for room in rooms}

        folio_ids = self.mapped("folio_id").ids
        existing_lines = FolioRoomLine.search(
            [("folio_id", "in", folio_ids), ("room_id", "in", rooms.ids)]
        )
        existing_map = {
            (line.folio_id.id, line.room_id.id): line for line in existing_lines
        }

        rooms_to_update = self.env["hotel.room"]
        vals_list = []
        for record in self:
            room = room_by_product.get(record.product_id.id)
            if not room:
                continue

            if (record.folio_id.id, room.id) not in existing_map:
                rooms_to_update |= room
                vals_list.append(
                    {
                        "room_id": room.id,
                        "check_in": record.checkin_date,
                        "check_out": record.checkout_date,
                        "folio_id": record.folio_id.id,
                    }
                )

        if rooms_to_update:
            rooms_to_update.write({"isroom": False})
        if vals_list:
            FolioRoomLine.create(vals_list)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override ORM create method to auto-link order_id
        from folio when folio_id is provided.
        """
        folio_ids = [v.get("folio_id") for v in vals_list if v.get("folio_id")]
        if folio_ids:
            folios = self.env["hotel.folio"].browse(folio_ids)
            folio_to_order = {folio.id: folio.order_id.id for folio in folios}
            for vals in vals_list:
                folio_id = vals.get("folio_id")
                if folio_id and folio_id in folio_to_order:
                    vals["order_id"] = folio_to_order[folio_id]

        lines = super().create(vals_list)
        lines._update_folio_line()
        return lines

    @api.constrains("checkin_date", "checkout_date")
    def _check_dates(self):
        """
        This method is used to validate the checkin_date and checkout_date.
        -------------------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        for rec in self:
            if rec.checkin_date >= rec.checkout_date:
                raise ValidationError(
                    _(
                        """Room line Check In Date Should be """
                        """less than the Check Out Date!"""
                    )
                )
            if rec.folio_id.date_order and rec.checkin_date:
                if rec.checkin_date.date() < rec.folio_id.date_order.date():
                    raise ValidationError(
                        _(
                            """Room line check-in date should be """
                            """greater than the folio order date."""
                        )
                    )

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """

        hotel_room_obj = self.env["hotel.room"]
        hotel_room_line_obj = self.env["folio.room.line"]

        product_ids = self.mapped("product_id").ids
        rooms = hotel_room_obj.search([("product_id", "in", product_ids)])

        domain = []
        for line in self:
            if line.product_id:
                line_rooms = rooms.filtered(
                    lambda r, pid=line.product_id.id: r.product_id.id == pid
                )
                if line_rooms:
                    domain = expression.OR(
                        [
                            domain,
                            [
                                ("folio_id", "=", line.folio_id.id),
                                ("room_id", "in", line_rooms.ids),
                            ],
                        ]
                    )

        if domain:
            folio_room_lines = hotel_room_line_obj.search(domain)
            if folio_room_lines:
                folio_room_lines.unlink()

        if rooms:
            rooms.write({"isroom": True, "status": "available"})

        return super().unlink()

    # # Migrated _onchange_product_id method v15 to v18.
    @api.onchange("product_id")
    def _onchange_product_id_warning(self):
        self.ensure_one()
        if not self.product_id or not self.order_line_id:
            return
        product = self.product_id
        # if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
        vals = {
            "name": self.product_id.name,
            "product_uom": self.product_id.uom_id,
            "product_uom_qty": self.product_uom_qty,
            "price_unit": self.product_id.list_price,
            "tax_id": self.product_id.taxes_id,
        }
        self.update(vals)

        if product.sale_line_warn != "no-message":
            if product.sale_line_warn == "block":
                self.product_id = False

            return {
                "warning": {
                    "title": _("Warning for %s", product.name),
                    "message": product.sale_line_warn_msg,
                }
            }

    @api.onchange("checkin_date", "checkout_date")
    def _onchange_checkin_checkout_dates(self):
        """
        When you change checkin_date or checkout_date it will check it
        and update the quantity of hotel folio line
        -----------------------------------------------------------------
        @param self: object pointer
        """

        configured_addition_hours = (
            self.folio_id.warehouse_id.company_id.additional_hours
        )
        myduration = 0
        if self.checkin_date and self.checkout_date:
            dur = self.checkout_date - self.checkin_date
            sec_dur = dur.seconds
            if (not dur.days and not sec_dur) or (dur.days and not sec_dur):
                myduration = dur.days
            else:
                myduration = dur.days + 1
            #            To calculate additional hours in hotel room as per minutes
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    myduration += 1
        self.product_uom_qty = myduration

    def copy_data(self, default=None):
        """
        @param self: object pointer
        @param default: dict of default values to be set
        """

        sale_line_obj = self.order_line_id
        return sale_line_obj.copy_data(default=default)
