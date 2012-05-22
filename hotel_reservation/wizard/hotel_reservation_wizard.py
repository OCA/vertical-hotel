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

class hotel_reservation_wizard(osv.osv_memory):
    
    _name = 'hotel.reservation.wizard'
    
    _columns = {
        'date_start' :fields.datetime('Start Date',required=True),
        'date_end': fields.datetime('End Date',required=True),        
    }
    
    def report_reservation_detail(self,cr,uid,ids,context=None):    
        if context is None:
            context = {}
            
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, context=context)
        res = res and res[0] or {}
        datas['form'] = res
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'reservation.detail',
            'datas': datas,
        }
    
    def report_checkin_detail(self,cr,uid,ids,context=None):    
        if context is None:
            context = {}
            
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, context=context)
        res = res and res[0] or {}
        datas['form'] = res
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'checkin.detail',
            'datas': datas,
        }
    
    def report_checkout_detail(self,cr,uid,ids,context=None):    
        if context is None:
            context = {}
            
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, context=context)
        res = res and res[0] or {}
        datas['form'] = res
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'checkout.detail',
            'datas': datas,
        }
        
    def report_maxroom_detail(self,cr,uid,ids,context=None):    
        if context is None:
            context = {}
            
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, context=context)
        res = res and res[0] or {}
        datas['form'] = res
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'maxroom.detail',
            'datas': datas,
        }
      
hotel_reservation_wizard()

class make_folio_wizard(osv.osv_memory):
    
    _name = 'wizard.make.folio'
    
    _columns = {
        'grouped':fields.boolean('Group the Folios'),
    }
    
    _defaults = {  
        'grouped': False,
    }
    
    def makeFolios(self, cr, uid, data, context):
        order_obj = self.pool.get('hotel.reservation')
        newinv = []
        for o in order_obj.browse(cr, uid, context['active_ids'], context):
            for i in o.folio_id:
               newinv.append(i.id)
        return {
            'domain': "[('id','in', ["+','.join(map(str,newinv))+"])]",
            'name': 'Folios',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hotel.folio',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }

    
make_folio_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
