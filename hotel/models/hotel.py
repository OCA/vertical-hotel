# -*- encoding: utf-8 -*-
from openerp.osv import fields
import time
from openerp import netsvc, models, fields, api
from mx import DateTime
import datetime
from openerp.tools import config


class hotel_floor(models.Model):
    _name = "hotel.floor"
    _description = "Floor"
    name = fields.Char('Floor Name', size=64, required=True, select=True)
    sequence = fields.Integer('Sequence', size=64)

class product_category(models.Model):
    _inherit = "product.category"
    isroomtype = fields.Boolean('Is Room Type')
    isamenitype = fields.Boolean('Is amenities Type')
    isservicetype = fields.Boolean('Is Service Type')

class hotel_room_type(models.Model):
    _name = "hotel.room.type"
    _inherits = {'product.category':'cat_id'}
    _description = "Room Type"
    cat_id = fields.Many2one('product.category', 'category', required=True, select=True, ondelete='cascade')

    _defaults = {
        'isroomtype': lambda * a: 1,
    }

class product_product(models.Model):
    _inherit = "product.product"
    isroom = fields.Boolean('Is Room')
    iscategid = fields.Boolean('Is categ id')
    isservice = fields.Boolean('Is Service id')


class hotel_room_amenities_type(models.Model):
    _name = 'hotel.room.amenities.type'
    _description = 'amenities Type'
    _inherits = {'product.category':'cat_id'}
    cat_id = fields.Many2one('product.category', 'category', required=True, ondelete='cascade')
    _defaults = {
        'isamenitype': lambda * a: 1,
        
    }


class hotel_room_amenities(models.Model):
    _name = 'hotel.room.amenities'
    _description = 'Room amenities'
    _inherits = {'product.product':'room_categ_id'}
    room_categ_id = fields.Many2one('product.product', 'Product Category', required=True, ondelete='cascade')
    rcateg_id = fields.Many2one('hotel.room.amenities.type', 'Amenity Category')
    amenity_rate = fields.Integer('Amenity Rate')

    _defaults = {
        'isamenitype': lambda * a: 1,
        }

class hotel_room(models.Model):
  
    _name = 'hotel.room'
    _inherits = {'product.product':'product_id'}
    _description = 'Hotel Room'
    product_id = fields.Many2one('product.product', 'Product_id', required=True, ondelete='cascade')
    floor_id = fields.Many2one('hotel.floor', 'Floor No')
    max_adult = fields.Integer('Max Adult')
    max_child = fields.Integer('Max Child')
    avail_status = fields.Selection([('assigned', 'Assigned'), (' unassigned', 'Unassigned')], 'Room Status')
    room_amenities = fields.Many2many('hotel.room.amenities', 'temp_tab', 'room_amenities', 'rcateg_id', 'Room Amenities')
    folio_id = fields.One2many('hotel.folio', 'room_id', 'Graph test')
    _defaults = {
        'isroom': lambda * a: 1,
        'rental': lambda * a: 1,
        }


class hotel_service_type(models.Model):
    _name = "hotel.service.type"
    _inherits = {'product.category':'ser_id'}
    _description = "Service Type" 
    ser_id = fields.Many2one(
        'product.category',
        string='Category',
        required=True,
        select=True,
        ondelete='cascade')
    _defaults = {
        'isservicetype': lambda * a: 1,
    }

class hotel_services(models.Model):
    
    _name = 'hotel.services'
    _description = 'Hotel Services and its charges'
    _inherits = {'product.product':'service_id'}
    service_id = fields.Many2one('product.product', string='Service', required=True, ondelete='cascade')
    _defaults = {
        'isservice': lambda * a: 1,
        }



