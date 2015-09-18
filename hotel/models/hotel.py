# -*- encoding: utf-8 -*-
from openerp import fields
from openerp import models


class HotelFloor(models.Model):
    _name = "hotel.floor"
    _description = "Floor"

    name = fields.Char('Floor Name',
                       size=64,
                       required=True,
                       select=True)

    sequence = fields.Integer('Sequence',
                              size=64)


class ProductCategory(models.Model):
    _inherit = "product.category"
    isroomtype = fields.Boolean('Is Room Type')
    isamenitype = fields.Boolean('Is amenities Type')
    isservicetype = fields.Boolean('Is Service Type')


class HotelRoomType(models.Model):
    _name = "hotel.room.type"
    _description = "Room Type"
    cat_id = fields.Many2one('product.category',
                             'category',
                             required=True,
                             select=True,
                             ondelete='cascade',
                             delegate=True)

    _defaults = {
        'isroomtype': lambda * a: 1,
    }


class ProductProduct(models.Model):
    _inherit = "product.product"
    isroom = fields.Boolean('Is Room')
    iscategid = fields.Boolean('Is categ id')
    isservice = fields.Boolean('Is Service id')


class HotelRoomAmenitiesType(models.Model):
    _name = 'hotel.room.amenities.type'
    _description = 'amenities Type'
    cat_id = fields.Many2one('product.category',
                             'category',
                             required=True,
                             ondelete='cascade',
                             delegate=True)
    _defaults = {
        'isamenitype': lambda * a: 1,

    }


class HotelRoomAmenities(models.Model):
    _name = 'hotel.room.amenities'
    _description = 'Room amenities'
    room_categ_id = fields.Many2one('product.product',
                                    'Product Category',
                                    required=True,
                                    ondelete='cascade',
                                    delegate=True)
    amenity_categ = fields.Many2one('hotel.room.amenities.type',
                                    'Amenity Category')
    amenity_rate = fields.Integer('Amenity Rate')

    _defaults = {
        'isamenitype': lambda * a: 1,
        }


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'

    product_id = fields.Many2one('product.product',
                                 'Product_id',
                                 required=True,
                                 ondelete='cascade',
                                 delegate=True)
    floor_id = fields.Many2one('hotel.floor',
                               'Floor No')
    max_adult = fields.Integer('Max Adult')
    max_child = fields.Integer('Max Child')
    avail_status = fields.Selection([('assigned', 'Assigned'),
                                     (' unassigned', 'Unassigned')],
                                    'Room Status')
    room_amenities = fields.Many2many('hotel.room.amenities',
                                      'temp_tab',
                                      'room_amenities',
                                      'amenity_categ',
                                      'Room Amenities')

    _defaults = {
        'isroom': lambda * a: 1,
        'rental': lambda * a: 1,
        }


class HotelServiceType(models.Model):
    _name = "hotel.service.type"
    _description = "Service Type"

    ser_id = fields.Many2one(
        'product.category',
        string='Category',
        required=True,
        select=True,
        ondelete='cascade',
        delegate=True)

    _defaults = {
        'isservicetype': lambda * a: 1,
    }


class HotelServices(models.Model):
    _name = 'hotel.services'
    _description = 'Hotel Services and its charges'

    service_id = fields.Many2one('product.product',
                                 string='Service',
                                 required=True,
                                 ondelete='cascade',
                                 delegate=True)

    _defaults = {
        'isservice': lambda * a: 1,
        }
