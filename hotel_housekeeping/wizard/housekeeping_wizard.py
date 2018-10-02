# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HotelHousekeepingWizard(models.TransientModel):
    _name = 'hotel.housekeeping.wizard'

    date_start = fields.Datetime('Activity Start Date', required=True)
    date_end = fields.Datetime('Activity End Date', required=True)
    room_id = fields.Many2one('hotel.room', 'Room No', required=True)

    @api.multi
    def print_report(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.housekeeping',
            'form': self.read(['date_start', 'date_end', 'room_id'])[0]
        }
        return self.env.ref('hotel_housekeeping.report_hotel_housekeeping').\
            report_action(self, data=data)
