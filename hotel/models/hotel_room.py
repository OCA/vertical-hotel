# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HotelFloor(models.Model):
    _name = "hotel.floor"
    _description = "Floor"

    name = fields.Char("Floor Name", required=True, index=True)
    sequence = fields.Integer(index=True)


class HotelRoom(models.Model):
    _name = "hotel.room"
    _description = "Hotel Room"

    product_id = fields.Many2one(
        "product.product",
        "Product_id",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    floor_id = fields.Many2one(
        "hotel.floor", "Floor No", help="At which floor the room is located."
    )
    max_adult = fields.Integer()
    max_child = fields.Integer()
    room_categ_id = fields.Many2one(
        "hotel.room.type",
        "Room Category",
        required=True,
        oldname="categ_id",
        ondelete="restrict",
    )
    room_amenities = fields.Many2many(
        "hotel.room.amenities",
        "temp_tab",
        "room_amenities",
        "rcateg_id",
        help="List of room amenities. ",
    )
    status = fields.Selection(
        [("available", "Available"), ("occupied", "Occupied")],
        "Status",
        default="available",
    )
    capacity = fields.Integer("Capacity", required=True)
    room_line_ids = fields.One2many(
        "folio.room.line", "room_id", string="Room Reservation Line"
    )
    product_manager = fields.Many2one("res.users", "Product Manager")

    @api.constrains("capacity")
    def check_capacity(self):
        for room in self:
            if room.capacity <= 0:
                raise ValidationError(_("Room capacity must be more than 0"))

    @api.onchange("isroom")
    def isroom_change(self):
        """
        Based on isroom, status will be updated.
        ----------------------------------------
        @param self: object pointer
        """
        if self.isroom is False:
            self.status = "occupied"
        if self.isroom is True:
            self.status = "available"

    @api.model
    def create(self, vals):
        if vals.get("room_categ_id", False):
            room_categ = self.env["hotel.room.type"].browse(
                vals.get("room_categ_id")
            )
            vals.update({"categ_id": room_categ.product_categ_id.id})
        return super(HotelRoom, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if vals.get("room_categ_id", False):
            room_categ = self.env["hotel.room.type"].browse(
                vals.get("room_categ_id")
            )
            vals.update({"categ_id": room_categ.product_categ_id.id})
        if "isroom" in vals and vals["isroom"] is False:
            vals.update({"color": 2, "status": "occupied"})
        if "isroom" in vals and vals["isroom"] is True:
            vals.update({"color": 5, "status": "available"})
        return super(HotelRoom, self).write(vals)

    @api.multi
    def set_room_status_occupied(self):
        """
        This method is used to change the state
        to occupied of the hotel room.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({"isroom": False, "color": 2})

    @api.multi
    def set_room_status_available(self):
        """
        This method is used to change the state
        to available of the hotel room.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({"isroom": True, "color": 5})
