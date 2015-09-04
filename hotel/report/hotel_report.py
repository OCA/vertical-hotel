# -*- coding: utf-8 -*-
from openerp import fields
from openerp import models
from openerp import tools


class hotel_report(models.Model):
    _name = "hotel.report"
    _description = "Hotel Report"
    _auto = False

    date_order = fields.Datetime('Date Order',
                                 readonly=True)

    product_id = fields.Many2one('product.product',
                                 'Product',
                                 readonly=True,)

    price_total = fields.Float('Total Price',
                               readonly=True)

    partner_id = fields.Many2one('res.partner',
                                 'Customer',
                                 readonly=True)

    checkin_date = fields.Datetime('Check In',
                                   readonly=True)

    checkout_date = fields.Datetime('Check Out',
                                    readonly=True)

    user_id = fields.Many2one('res.users', 'Salesperson',
                              readonly=True)

    categ_id = fields.Many2one('product.category',
                               'Category of Product',
                               readonly=True)

    product_uom = fields.Many2one('product.uom',
                                  'Unit of Measure',
                                  readonly=True)

    product_uom_qty = fields.Float('# of Qty',
                                   readonly=True)

    order_id = fields.Many2one('sale.order',
                               'Order',
                               readonly=True)

    def _select(self):
        select_str = """
             SELECT min(ol.id) as id,
                    ol.product_id as product_id,
                    t.uom_id as product_uom,
                    r.checkin_date,
                    r.checkout_date,
                    sum(ol.product_uom_qty / u.factor * u2.factor) \
                    as product_uom_qty,
                    sum(ol.product_uom_qty*ol.price_unit*(100.0-ol.discount)\
                     / 100.0) as price_total,
                    s.date_order as date_order,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    ol.state,
                    ol.order_id,
                    s.pricelist_id as pricelist_id
        """
        return select_str

    def _from(self):
        from_str = """
                    hotel_folio_room r,
                    sale_order_line ol
                    join sale_order s on (ol.order_id=s.id)
                        left join product_product p on (ol.product_id=p.id)
                            left join product_template t on \
                            (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=ol.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id),
                    hotel_folio f
                    where r.order_line_id = ol.id
                    and s.id = ol.order_id
                    and f.order_id = s.id
        """

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
                     t.uom_id,
                     ol.state,
                     ol.order_id,
                     s.pricelist_id
        """
        return group_by_str

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM %s
            %s
            )""" % (self._table,
                    self._select(),
                    self._from(),
                    self._group_by())
                   )
