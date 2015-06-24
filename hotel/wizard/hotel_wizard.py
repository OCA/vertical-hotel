# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

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


