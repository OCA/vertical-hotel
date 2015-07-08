# -*- encoding: utf-8 -*-

from openerp.osv import fields
from openerp import netsvc, models, fields, api
from mx import DateTime

class folio_report_wizard(models.TransientModel):
    
    _name = 'folio.report.wizard'
    
    _rec_name = 'date_start'
    date_start = fields.Datetime('Start Date')
    date_end = fields.Datetime('End Date')

    @api.multi
    def print_report(self):
        datas = {
             'ids': self.ids,
             'model': 'hotel.folio',
             'form': self.read(self.ids)[0]
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'folio.total',
            'datas': datas,
        }


