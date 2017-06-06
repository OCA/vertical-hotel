# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name' : 'Hotel Reservation Management - Reporting',
    'version' : '10.0.1.0.0',
    'author' : 'Tiny,Odoo Community Association (OCA),Serpent Consulting\
                Services Pvt. Ltd., OpenERP SA',
    'website': 'http://www.serpentcs.com',
    'license': 'AGPL-3',
    'depends' : ['hotel_reservation'],
    'category' : 'Generic Modules/Hotel Reservation',
     'description': '''
                    Module shows the status of room reservation
                    * Current status of reserved room
                    * List status of room as draft or done state
    ''',
    'data': [
        'security/ir.model.access.csv',
        'views/report_hotel_reservation_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
