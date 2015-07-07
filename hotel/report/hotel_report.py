# -*- encoding: utf-8 -*-

import time
from openerp.report import report_sxw
from openerp import pooler
import datetime
class folio_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(folio_report, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'get_data': self.get_data,
            'get_Total' : self.getTotal,
            'get_total': self.gettotal,
        })
        self.context=context
        self.temp = 0.0

    def get_data(self,date_start,date_end):
        #print date_start
        tids = self.pool.get('hotel.folio').search(self.cr,self.uid,[('checkin_date', '>=', date_start),('checkout_date', '<=', date_end)])
        res = self.pool.get('hotel.folio').browse(self.cr,self.uid,tids)
        return res
    
    def gettotal(self,total):
        self.temp = self.temp + float(total)
        return total
    
    def getTotal(self):
        return self.temp
        
report_sxw.report_sxw('report.folio.total', 'hotel.folio', 'addons/hotel/report/total_folio.rml',parser= folio_report)               