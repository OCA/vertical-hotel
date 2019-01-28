# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HotelHousekeeping(models.Model):

    _name = "hotel.housekeeping"
    _description = "Reservation"
    _rec_name = 'room_no'

    current_date = fields.Date("Today's Date", required=True,
                               index=True,
                               states={'done': [('readonly', True)]},
                               default=fields.Date.today)
    clean_type = fields.Selection([('daily', 'Daily'),
                                   ('checkin', 'Check-In'),
                                   ('checkout', 'Check-Out')],
                                  'Clean Type', required=True,
                                  states={'done': [('readonly', True)]},)
    room_no = fields.Many2one('hotel.room', 'Room No', required=True,
                              states={'done': [('readonly', True)]},
                              index=True)
    activity_line_ids = fields.One2many('hotel.housekeeping.activities',
                                        'a_list', 'Activities',
                                        states={'done': [('readonly', True)]},
                                        help='Detail of housekeeping'
                                        'activities')
    inspector_id = fields.Many2one('res.users', 'Inspector', required=True,
                                   index=True,
                                   states={'done': [('readonly', True)]})
    inspect_date_time = fields.Datetime('Inspect Date Time', required=True,
                                        states={'done': [('readonly', True)]})
    quality = fields.Selection([('excellent', 'Excellent'), ('good', 'Good'),
                                ('average', 'Average'), ('bad', 'Bad'),
                                ('ok', 'Ok')], 'Quality',
                               states={'done': [('readonly', True)]},
                               help="Inspector inspect the room and mark \
                                as Excellent, Average, Bad, Good or Ok. ")
    state = fields.Selection([('inspect', 'Inspect'), ('dirty', 'Dirty'),
                              ('clean', 'Clean'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')], 'State',
                             states={'done': [('readonly', True)]},
                             index=True, required=True, readonly=True,
                             default='inspect')

    @api.multi
    def action_set_to_dirty(self):
        """
        This method is used to change the state
        to dirty of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({
            'state': 'dirty',
            'quality': False
        })
        self.activity_line_ids.write({
            'clean': False,
            'dirty': True,
        })

    @api.multi
    def room_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({'state': 'cancel', 'quality': False})

    @api.multi
    def room_done(self):
        """
        This method is used to change the state
        to done of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        if not self.quality:
            raise ValidationError(_('Please update quality of work!'))
        self.state = 'done'

    @api.multi
    def room_inspect(self):
        """
        This method is used to change the state
        to inspect of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({'state': 'inspect', 'quality': False})

    @api.multi
    def room_clean(self):
        """
        This method is used to change the state
        to clean of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.write({
            'state': 'clean',
            'quality': False
        })
        self.activity_line_ids.write({
            'clean': True,
            'dirty': False,
        })
