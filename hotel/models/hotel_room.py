# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class HotelFloor(models.Model):

    _name = "hotel.floor"
    _description = "Floor"
    _order = "sequence"

    name = fields.Char("Floor Name", required=True, index=True)
    sequence = fields.Integer("sequence", default=10)


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
        "hotel.room.amenities", string="Room Amenities", help="List of room amenities."
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

    @api.model
    def create(self, vals):
        if "room_categ_id" in vals:
            room_categ = self.env["hotel.room.type"].browse(vals.get("room_categ_id"))
            vals.update({"categ_id": room_categ.product_categ_id.id})
        return super(HotelRoom, self).create(vals)

    @api.constrains("capacity")
    def _check_capacity(self):
        for room in self:
            if room.capacity <= 0:
                raise ValidationError(_("Room capacity must be more than 0"))

    @api.onchange("isroom")
    def _isroom_change(self):
        """
        Based on isroom, status will be updated.
        ----------------------------------------
        @param self: object pointer
        """
        if self.isroom is False:
            self.status = "occupied"
        if self.isroom is True:
            self.status = "available"

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
        return super(HotelRoom, self).write(vals)

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

    categ_id = fields.Many2one("hotel.room.type", "Category")
    child_ids = fields.One2many("hotel.room.type", "categ_id", "Room Child Categories")
    product_categ_id = fields.Many2one(
        "product.category", "Product Category", delegate=True, required=True, copy=False
    )

    @api.model
    def create(self, vals):
        if "categ_id" in vals:
            room_categ = self.env["hotel.room.type"].browse(vals.get("categ_id"))
            vals.update({"parent_id": room_categ.product_categ_id.id})
        return super(HotelRoomType, self).create(vals)

    def write(self, vals):
        if "categ_id" in vals:
            room_categ = self.env["hotel.room.type"].browse(vals.get("categ_id"))
            vals.update({"parent_id": room_categ.product_categ_id.id})
        return super(HotelRoomType, self).write(vals)

    def name_get(self):
        def get_names(cat):
            """Return the list [cat.name, cat.categ_id.name, ...]"""
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.categ_id
            return res

        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        if not args:
            args = []
        if name:
            # Be sure name_search is symmetric to name_get
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
                        [[("categ_id", "in", categories.ids)], domain]
                    )
                else:
                    domain = expression.AND(
                        [[("categ_id", "in", category_ids)], domain]
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
            categories = self.search(expression.AND([domain, args]), limit=limit)
        else:
            categories = self.search(args, limit=limit)
        return categories.name_get()


class HotelRoomAmenitiesType(models.Model):

    _name = "hotel.room.amenities.type"
    _description = "amenities Type"

    amenity_id = fields.Many2one("hotel.room.amenities.type", "Category")
    child_ids = fields.One2many(
        "hotel.room.amenities.type", "amenity_id", "Amenities Child Categories"
    )
    product_categ_id = fields.Many2one(
        "product.category", "Product Category", delegate=True, required=True, copy=False
    )

    @api.model
    def create(self, vals):
        if "amenity_id" in vals:
            amenity_categ = self.env["hotel.room.amenities.type"].browse(
                vals.get("amenity_id")
            )
            vals.update({"parent_id": amenity_categ.product_categ_id.id})
        return super(HotelRoomAmenitiesType, self).create(vals)

    def write(self, vals):
        if "amenity_id" in vals:
            amenity_categ = self.env["hotel.room.amenities.type"].browse(
                vals.get("amenity_id")
            )
            vals.update({"parent_id": amenity_categ.product_categ_id.id})
        return super(HotelRoomAmenitiesType, self).write(vals)

    def name_get(self):
        def get_names(cat):
            """Return the list [cat.name, cat.amenity_id.name, ...]"""
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.amenity_id
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
                        [[("amenity_id", "in", categories.ids)], domain]
                    )
                else:
                    domain = expression.AND(
                        [[("amenity_id", "in", category_ids)], domain]
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
            categories = self.search(expression.AND([domain, args]), limit=limit)
        else:
            categories = self.search(args, limit=limit)
        return categories.name_get()


class HotelRoomAmenities(models.Model):

    _name = "hotel.room.amenities"
    _description = "Room amenities"

    product_id = fields.Many2one(
        "product.product",
        "Room Amenities Product",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    amenities_categ_id = fields.Many2one(
        "hotel.room.amenities.type",
        "Amenities Category",
        required=True,
        ondelete="restrict",
    )
    product_manager = fields.Many2one("res.users", "Product Manager")

    @api.model
    def create(self, vals):
        if "amenities_categ_id" in vals:
            amenities_categ = self.env["hotel.room.amenities.type"].browse(
                vals.get("amenities_categ_id")
            )
            vals.update({"categ_id": amenities_categ.product_categ_id.id})
        return super(HotelRoomAmenities, self).create(vals)

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
        return super(HotelRoomAmenities, self).write(vals)
