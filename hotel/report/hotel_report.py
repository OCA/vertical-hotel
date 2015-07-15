from openerp import fields
from openerp import models
from openerp import tools
from openerp.tools.translate import _
from mx import DateTime

class hotel_report(models.Model):
    _name = "hotel.report"
    _description = "Hotel Report"
    _auto = False
    
    date_order = fields.Datetime('Date Order',
                                 readonly = True)
       
    product_id = fields.Many2one('product.product',
                                 'Product',
                                 readonly = True,)
    
    price_total = fields.Float('Total Price',
                                 readonly=True)
    
    partner_id = fields.Many2one('res.partner',
                                 'Customer',
                                 readonly = True)
    
    checkin_date = fields.Datetime('Check In',
                                   readonly = True)
    
    checkout_date = fields.Datetime('Check Out',
                                    readonly = True)
    
    user_id = fields.Many2one('res.users', 'Salesperson',
                               readonly=True)
    
    categ_id = fields.Many2one('product.category',
                               'Category of Product',
                               readonly=True)
    
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 readonly=True)
    
    product_uom = fields.Many2one('product.uom',
                                  'Unit of Measure',
                                  readonly=True)
    
    product_uom_qty = fields.Float('# of Qty',
                                   readonly=True)
    
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account',
                                          readonly=True)
    
    section_id = fields.Many2one('crm.case.section',
                                  'Sales Team')
    

    '''def init(self,cr):
        room_array = []
        query = """SELECT o.partner_id as Customer_ID, o.name, ol.product_id as product_id, r.checkin_date, \
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

        return array'''
    
    def _select(self):
        select_str = """
             SELECT min(ol.id) as id,
                    ol.product_id as product_id,
                    r.checkin_date,
                    r.checkout_date,
                    sum(ol.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(ol.product_uom_qty * ol.price_unit * (100.0-ol.discount) / 100.0) as price_total,
                    s.date_order as date_order,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    ol.state,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.project_id as analytic_account_id,
                    s.section_id as section_id
        """
        return select_str

    def _from(self):
        from_str = """
                    hotel_folio_room r,
                    sale_order_line ol
                    join sale_order s on (ol.order_id=s.id)
                        left join product_product p on (ol.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=ol.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id),
                    hotel_folio f
                    where r.order_line_id = ol.id
                    and s.id = ol.order_id
                    and f.order_id = s.id
        """
        '''order con folio
        orderline con folio room right join?'''
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY 
                     s.name,
                     ol.product_id,
                     r.checkin_date,
                     r.checkout_date,
                     s.date_order,
                     s.partner_id,
                     s.user_id,
                     s.company_id,
                     ol.state,
                     t.categ_id,
                     s.pricelist_id,
                     s.project_id,
                     s.section_id
              
        """
        return group_by_str

    def init(self, cr):
        #self._table = hotel_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM %s
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

    