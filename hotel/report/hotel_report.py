from openerp import fields
from openerp import models
from openerp import _
from mx import DateTime

class hotel_report(models.Model):
    #_name = "hotel.report"
    _inherit = 'hotel.folio'
    _description = "Hotel Report"
    _auto = False
    
    '''date_order = fields.Datetime('Date Order',
                                 readonly = True)
       
    product_id = fields.Many2one('product.product',
                                 'Product',
                                 readonly = True,)
    
    partner_id = fields.Many2one('res.partner',
                                 'Customer',
                                 readonly = True)
    
    checkin_date = fields.Datetime('Check In',
                                   readonly = True)
    
    chekcout_date = fields.Datetime('Check Out',
                                    readonly = True)'''
    

    def init(self,cr):
        room_array = []
        query = """SELECT o.partner_id as Customer_ID, o.name, ol.product_id as Room_ID, r.checkin_date, \
                    r.checkout_date \
                    FROM hotel_folio_room r, \
                    sale_order_line ol, \
                    sale_order o, \
                    hotel_folio f \
                    where r.order_line_id = ol.id \
                    and o.id = ol.order_id \
                    and f.order_id = o.id"""
        
        cr.execute(query)
        res = cr.fetchall()
        for row in res:
            room_array.append(row[2])
        #print room_array
        
        self._room_array(room_array)

    
    def _room_array(self, array):

        return array
    