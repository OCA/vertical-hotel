# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name' : 'Restaurant Management - Reporting',
    'version' : '10.0.1.0.0',
    'author' : 'Tiny,Odoo Community Association (OCA), Serpent Consulting\
                Services Pvt. Ltd., OpenERP SA',
    'website': 'http://www.serpentcs.com, http://www.openerp.com',
    'license': 'AGPL-3',
    'depends' : ['hotel_restaurant', 'report_hotel_reservation'],
    'category' : 'Generic Modules/Hotel Restaurant',
    'description': '''
                    Module shows the status of resturant reservation
                    * Current status of reserved tables
                    * List status of tables as draft or done state
    ''',
    'data' : ['security/ir.model.access.csv',
              'views/report_hotel_restaurant_view.xml'],
    'installable': True,
    'auto_install': False,
}
