from odoo import models, fields


class Contacts(models.Model):
    """ Calendar filter """

    _name = 'folio.room.partner.filter'
    _description = 'Hotel partners'

    user_id = fields.Many2one('res.users', 'Me', required=True, default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', 'Employee', required=True)
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('user_id_partner_id_unique', 'UNIQUE(user_id, partner_id)', 'You cannot have the same partner twice.')]


class Rooms(models.Model):
    """ Calendar filter """

    _name = 'folio.room.room.filter'
    _description = 'Rooms'

    user_id = fields.Many2one('res.users', 'Me', required=True, default=lambda self: self.env.user)
    room_id = fields.Many2one('hotel.room', 'Employee', required=True)
    active = fields.Boolean('Active', default=True)
