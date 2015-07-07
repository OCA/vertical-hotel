# -*- encoding: utf-8 -*-

import time
from openerp.report import report_sxw
import datetime
from openerp import pooler, api
from openerp import netsvc, models, fields

class folio_report(report_sxw.rml_parse):
    
    @api.one
    def __init__(self, name):
        super(folio_report, self).__init__(name)
        self.localcontext.update( {
            'time': time,
            'get_data': self.get_data,
            'get_Total' : self.getTotal,
            'get_total': self.gettotal,
        })
        self.temp = 0.0
        
    
    @api.model
    def get_data(self, date_start, date_end):
        print 'holaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        #folio_obj = self.env['hotel.folio']
        #partner_obj = self.env['res.partner']
        tids = self.env['hotel.folio'].search([('checkin_date', '>=', date_start), ('checkout_date', '<=', date_end)])
        res = self.env['hotel.folio'].browse(tids)    
        #res1 = partner_obj.browse(tids)
        return res
    
    '''@api.one
    def get_data(self, date_start, date_end):
        tids = self.env['hotel.folio'].search([('checkin_date', '>=', date_start),('checkout_date', '<=', date_end)])
        print tids
        res = self.env['hotel.folio'].browse(tids)
        return res'''
    
    @api.one
    def gettotal(self, total):
        self.temp = self.temp + float(total)
        return total
    
    @api.one
    def getTotal(self):
        return self.temp
        
        
class report_lunchorder(models.AbstractModel):
    _name = 'report.hotel.report_hotel_folio'
    _inherit = 'report.abstract_report'
    _template = 'hotel.report_hotel_folio'
    _wrapped_report_class = folio_report
#report_sxw.report_sxw('report.folio.total', 'hotel.folio', 'addons/hotel/report/total_folio.rml',parser= folio_report)             



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:                 