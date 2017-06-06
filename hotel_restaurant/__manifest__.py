# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name' : 'Hotel Restaurant Management',
    'version' : '10.0.1.0.0',
    'author' : 'Tiny,Odoo Community Association (OCA), Serpent Consulting\
                Services Pvt. Ltd., OpenERP SA',
    'category' : 'Generic Modules/Hotel Restaurant',
    'website': 'http://www.serpentcs.com',
    'license': 'AGPL-3',
    'description': '''Module for Hotel/Resort/Restaurant management.
                    You can manage:
                    * Configure Property
                    * Restaurant Configuration
                    * Table Reservation
                    * Generate and Process Kitchen Order Ticket,
                    * Payment
                    Different reports are also provided, mainly for
                    Restaurant. ''',
    'depends' : ['base', 'hotel'],
    'demo': ['views/hotel_restaurant_data.xml', ],
    'data': ['security/ir.model.access.csv',
             'report/hotel_restaurant_report.xml',
             'wizard/hotel_restaurant_wizard.xml',
             'views/res_table.xml',
             'views/kot.xml',
             'views/bill.xml',
             'views/folio_order_report.xml',
            'views/hotel_restaurant_sequence.xml',
            'views/hotel_restaurant_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
