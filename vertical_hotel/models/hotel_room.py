# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import ClassVar

from odoo import api, fields, models
from odoo.exceptions import ValidationError


def hierarchical_name_domain(parent_field, operator, value):
    """Domain for a "Parent / Child" search on a category tree linked by
    ``parent_field``: the last segment is matched with ``operator``, every
    parent segment must be the exact (case-insensitive) parent name."""
    *parents, child = (part.strip() for part in value.split(" / "))
    domain = [("name", operator, child)]
    path = parent_field
    for name in reversed(parents):
        domain.append((f"{path}.name", "=ilike", name))
        path = f"{path}.{parent_field}"
    return domain


def is_hierarchical_search(operator, value):
    return (
        operator in ("ilike", "like", "=", "=ilike", "=like")
        and isinstance(value, str)
        and " / " in value
    )


class HotelFloor(models.Model):
    _name = "hotel.floor"
    _description = "Floor"
    _order = "sequence"

    name = fields.Char("Floor Name", required=True, index=True)
    sequence = fields.Integer("sequence", default=10)


class HotelRoom(models.Model):
    _name = "hotel.room"
    _description = "Hotel Room"
    _inherits: ClassVar[dict] = {"product.product": "product_id"}

    product_id = fields.Many2one(
        "product.product",
        "Product_id",
        required=True,
        ondelete="cascade",
    )
    floor_id = fields.Many2one(
        "hotel.floor",
        "Floor No",
        help="At which floor the room is located.",
        ondelete="restrict",
    )
    max_adult = fields.Integer()
    max_child = fields.Integer()
    room_categ_id = fields.Many2one(
        "hotel.room.type", "Room Category", required=True, ondelete="restrict"
    )
    room_amenities_ids = fields.Many2many(
        "hotel.room.amenities", help="List of room amenities."
    )
    status = fields.Selection(
        [("available", "Available"), ("occupied", "Occupied")],
        default="available",
    )
    capacity = fields.Integer(required=True)
    room_line_ids = fields.One2many(
        "folio.room.line", "room_id", string="Room Reservation Line"
    )
    product_manager = fields.Many2one("res.users")

    @api.model_create_multi
    def create(self, vals_list):
        room_type_obj = self.env["hotel.room.type"]
        for vals in vals_list:
            if not vals.get("product_id"):
                # sold, never delivered: no delivery order on confirmation
                vals.setdefault("type", "service")
            if "room_categ_id" in vals:
                room_categ = room_type_obj.browse(vals.get("room_categ_id"))
                vals.update({"categ_id": room_categ.product_categ_id.id})
        return super().create(vals_list)

    @api.constrains("capacity")
    def _check_capacity(self):
        for room in self:
            if room.capacity <= 0:
                raise ValidationError(room.env._("Room capacity must be more than 0"))

    @api.onchange("isroom")
    def _onchange_isroom(self):
        """
        Based on isroom, status will be updated.
        ----------------------------------------
        @param self: object pointer
        """
        self.status = "available" if self.isroom else "occupied"

    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if "room_categ_id" in vals:
            room_categ = self.env["hotel.room.type"].browse(vals.get("room_categ_id"))
            vals.update({"categ_id": room_categ.product_categ_id.id})
        if "isroom" in vals and vals["isroom"] is False:
            vals.update({"color": 2, "status": "occupied"})
        if "isroom" in vals and vals["isroom"] is True:
            vals.update({"color": 5, "status": "available"})
        return super().write(vals)

    def set_room_status_occupied(self):
        """
        This method is used to change the state
        to occupied of the hotel room.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({"isroom": False, "color": 2})

    def set_room_status_available(self):
        """
        This method is used to change the state
        to available of the hotel room.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({"isroom": True, "color": 5})


class HotelRoomType(models.Model):
    _name = "hotel.room.type"
    _description = "Room Type"
    _inherits: ClassVar[dict] = {"product.category": "product_categ_id"}
    _rec_name = "name"

    categ_id = fields.Many2one("hotel.room.type", "Category")
    child_ids = fields.One2many("hotel.room.type", "categ_id", "Room Child Categories")
    product_categ_id = fields.Many2one(
        "product.category",
        "Product Category",
        required=True,
        copy=False,
        ondelete="restrict",
    )

    @api.model_create_multi
    def create(self, vals_list):
        room_type_obj = self.env["hotel.room.type"]
        for vals in vals_list:
            if "categ_id" in vals:
                room_categ = room_type_obj.browse(vals.get("categ_id"))
                vals.update({"parent_id": room_categ.product_categ_id.id})
        return super().create(vals_list)

    def write(self, vals):
        if "categ_id" in vals:
            room_categ = self.env["hotel.room.type"].browse(vals.get("categ_id"))
            vals.update({"parent_id": room_categ.product_categ_id.id})
        return super().write(vals)

    def _compute_display_name(self):
        def get_names(cat):
            """Return the list [cat.name, cat.categ_id.name, ...]"""
            res = []
            while cat:
                if cat.name:
                    res.append(cat.name)
                cat = cat.categ_id
            return res

        for cat in self:
            cat.display_name = " / ".join(reversed(get_names(cat))) or ""

    @api.model
    def _search_display_name(self, operator, value):
        if is_hierarchical_search(operator, value):
            return hierarchical_name_domain("categ_id", operator, value)
        return super()._search_display_name(operator, value)


class HotelRoomAmenitiesType(models.Model):
    _name = "hotel.room.amenities.type"
    _description = "amenities Type"
    _inherits: ClassVar[dict] = {"product.category": "product_categ_id"}
    _order = "name"

    amenity_id = fields.Many2one("hotel.room.amenities.type", "Category")
    child_ids = fields.One2many(
        "hotel.room.amenities.type", "amenity_id", "Amenities Child Categories"
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
        rm_amenity_obj = self.env["hotel.room.amenities.type"]
        for vals in vals_list:
            if "amenity_id" in vals:
                amenity_categ = rm_amenity_obj.browse(vals.get("amenity_id"))
                vals.update({"parent_id": amenity_categ.product_categ_id.id})
        return super().create(vals_list)

    def write(self, vals):
        if "amenity_id" in vals:
            amenity_categ = self.env["hotel.room.amenities.type"].browse(
                vals.get("amenity_id")
            )
            vals.update({"parent_id": amenity_categ.product_categ_id.id})
        return super().write(vals)

    def _compute_display_name(self):
        def get_names(cat):
            """Return the list [cat.name, cat.amenity_id.name, ...]"""
            res = []
            while cat:
                if cat.name:
                    res.append(cat.name)
                cat = cat.amenity_id
            return res

        for cat in self:
            cat.display_name = " / ".join(reversed(get_names(cat))) or ""

    @api.model
    def _search_display_name(self, operator, value):
        if is_hierarchical_search(operator, value):
            return hierarchical_name_domain("amenity_id", operator, value)
        return super()._search_display_name(operator, value)


class HotelRoomAmenities(models.Model):
    _name = "hotel.room.amenities"
    _description = "Room amenities"
    _inherits: ClassVar[dict] = {"product.product": "product_id"}

    product_id = fields.Many2one(
        "product.product",
        "Room Amenities Product",
        required=True,
        ondelete="cascade",
    )
    amenities_categ_id = fields.Many2one(
        "hotel.room.amenities.type",
        "Amenities Category",
        required=True,
        ondelete="restrict",
    )
    product_manager = fields.Many2one("res.users")

    @api.model_create_multi
    def create(self, vals_list):
        rm_amenity_obj = self.env["hotel.room.amenities.type"]
        for vals in vals_list:
            if "amenities_categ_id" in vals:
                amenities_categ = rm_amenity_obj.browse(vals.get("amenities_categ_id"))
                vals.update({"categ_id": amenities_categ.product_categ_id.id})
        return super().create(vals_list)

    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if "amenities_categ_id" in vals:
            amenities_categ = self.env["hotel.room.amenities.type"].browse(
                vals.get("amenities_categ_id")
            )
            vals.update({"categ_id": amenities_categ.product_categ_id.id})
        return super().write(vals)
