# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class WizardHotelRestaurant(models.TransientModel):

    _name = 'wizard.hotel.restaurant'

    date_start = fields.Datetime('Start Date', required=True)
    date_end = fields.Datetime('End Date', required=True)

    @api.multi
    def print_report(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.restaurant.reservation',
            'form': self.read(['date_start', 'date_end'])[0]
        }
        return self.env.ref('hotel_restaurant.report_hotel_table_res').\
            report_action(self, data=data)


class FolioRestReservation(models.TransientModel):
    _name = 'folio.rest.reservation'
    _rec_name = 'date_start'

    date_start = fields.Datetime('Start Date')
    date_end = fields.Datetime('End Date')
    check = fields.Boolean('With Details')

    @api.multi
    def print_rest_report(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.folio',
            'form': self.read(['date_start', 'date_end', 'check'])[0]
        }
        return self.env.ref('hotel_restaurant.report_hotel_res_folio').\
            report_action(self, data=data)

    @api.multi
    def print_reserv_report(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.folio',
            'form': self.read(['date_start', 'date_end', 'check'])[0]
        }
        return self.env.ref('hotel_restaurant.report_hotel_res_folio1').\
            report_action(self, data=data)
