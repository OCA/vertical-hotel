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

from osv import fields
from osv import osv
import time
from mx import DateTime
import datetime
import pooler
from tools import config
import wizard
import netsvc
import pooler

class wizard_hotel_restaurant(osv.osv_memory):
    
    _name = 'wizard.hotel.restaurant'
    
    _columns = {
        'date_start' :fields.datetime('Start Date',required=True),
        'date_end': fields.datetime('End Date',required=True),        
    }
    
    def print_report(self,cr,uid,ids,context=None):
        datas = {
             'ids': ids,
             'model': 'hotel.restaurant.reservation',
             'form': self.read(cr, uid, ids)[0]
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hotel.table.res',
            'datas': datas,
        }

wizard_hotel_restaurant()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: