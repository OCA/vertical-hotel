

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

from osv import osv, fields


class hotel_housekeeping_wizard(osv.osv_memory):
    _name = 'hotel.housekeeping.wizard'

    _columns = {
        'date_start': fields.date('Start Date', required=True),
        'date_end': fields.date('End Date', required=True),
        'room_no': fields.many2one('hotel.room', 'Room No.', required=True),
    }

    def print_report(self, cr, uid, ids, context=None):
        datas = {
            'ids': ids,
            'model': 'hotel.housekeeping',
            'form': self.read(cr, uid, ids)[0]
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'activity.detail',
            'datas': datas,
        }

hotel_housekeeping_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
