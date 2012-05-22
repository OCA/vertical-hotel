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

from osv import osv,fields

class folio_report_wizard(osv.osv_memory):
    
    _name = 'folio.report.wizard'
    
    _rec_name = 'date_start'
    _columns = {
                'date_start':fields.datetime('Start Date'),
                'date_end':fields.datetime('End Date')
                }
    
    def print_report(self,cr,uid,ids,context=None):
        
        if context is None:
            context = {}
            
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, context=context)
        res = res and res[0] or {}
        datas['form'] = res

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'folio.total',
            'datas': datas,
        }

        
folio_report_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

