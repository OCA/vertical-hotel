# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name' : 'Hotel Housekeeping Management',
    'version' : '10.0.1.0.0',
    'author' : 'Tiny,Odoo Community Association (OCA), Serpent Consulting\
                Services Pvt. Ltd., OpenERP SA',
    'website': 'http://www.serpentcs.com',
    'license': 'AGPL-3',
    'category' : 'Generic Modules/Hotel Housekeeping',
    'description': '''
                    Module for Hotel/Hotel Housekeeping. You can manage:
                    * Housekeeping process
                    * Housekeeping history room wise
                    Different reports are also provided, mainly for
                    hotel statistics.
    ''',
    'depends' : ['hotel'],
    'demo' : ['views/hotel_housekeeping_data.xml', ],
    'data': [
        'security/ir.model.access.csv',
        'report/hotel_housekeeping_report.xml',
        'views/activity_detail.xml',
        'wizard/hotel_housekeeping_wizard.xml',
        'views/hotel_housekeeping_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
