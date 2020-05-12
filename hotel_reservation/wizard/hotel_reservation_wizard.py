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
import ir
from mx import DateTime
import datetime
import pooler
from tools import config
import wizard
import netsvc


room_res_form= """<?xml version="1.0"?>
<form string="Reservation List">
     <field name="date_start" />
     <field name="date_end" />
</form>
"""

room_res_field= {
    'date_start': {'string':'Start Date','type':'datetime','required': True},
    'date_end': {'string':'End Date','type':'datetime','required': True},
    
}

room_result_form = """<?xml version="1.0"?>
<form string="Room Reservation">
    <separator string="Reservation List" />
</form>"""

result_fields = {}

class get_reservation_room_list(wizard.interface):

    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : room_res_form,
                    'fields' : room_res_field,
                    'state' : [('print_report', 'Reservation List'),('print_checkin', 'CheckIn List'),('print_checkout', 'CheckOut List'),('print_room_used','Room Used Maximum'),('end', 'Cancel')]}
        },
        'print_report' : {
            'actions' : [],
            'result' : {'type' : 'print',
                    'report':'reservation.detail',
                    'state' : 'end'}
        },
         'print_checkin' : {
            'actions' : [],
            'result' : {'type' : 'print',
                    'report':'checkin.detail',
                    'state' : 'end'}
        },
         'print_checkout' : {
            'actions' : [],
            'result' : {'type' : 'print',
                    'report':'checkout.detail',
                    'state' : 'end'}
        },
        'print_room_used': {
            'action' : [],
            'result' : {'type' : 'print',
                    'report':'maxroom.detail',
                    'state' : 'end'}             
        },    
    
       
    }
get_reservation_room_list("hotel.reservation.report_reservation")     

folio_form = """<?xml version="1.0"?>
<form string="Create Folio">
    <separator colspan="4" string="Do you really want to create the Folio ?" />
    <field name="grouped" />
</form>
"""
folio_fields = {
    'grouped' : {'string':'Group the Folios', 'type':'boolean', 'default': lambda x,y,z: False}
}

ack_form = """<?xml version="1.0"?>
<form string="Create Folios">
    <separator string="Folios created" />
</form>"""

ack_fields = {}

def _makeFolios(self, cr, uid, data, context):
    
    
    order_obj = pooler.get_pool(cr.dbname).get('hotel.reservation')
    newinv = []
    for o in order_obj.browse(cr, uid, data['ids'], context):
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
    return {}

class make_folio(wizard.interface):
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : folio_form,
                    'fields' : folio_fields,
                    'state' : [('end', 'Cancel'),('folio', 'Create Folios') ]}
        },
        'folio' : {
            'actions' : [_makeFolios],
            'result' : {'type' : 'action',
                    'action' : _makeFolios,
                    'state' : 'end'}
        },
    }
make_folio("hotel.folio.make_folio")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
