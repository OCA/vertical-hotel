# See LICENSE file for full copyright and licensing details.

{
    'name': 'Hotel Management',
    'version': '11.0.1.0.0',
    'author': 'Odoo Community Association (OCA), Serpent Consulting \
               Services Pvt. Ltd., OpenERP SA',
    'category': 'Generic Modules/Hotel Management',
    'website': 'https://github.com/OCA/vertical-hotel/',
    'depends': ['sale_stock', 'point_of_sale'],
    'license': 'AGPL-3',
    'summary': 'Hotel Management to Manage Folio and Hotel Configuration',
    'demo': ['views/hotel_data.xml'],
    'data': [
            'security/hotel_security.xml',
            'security/ir.model.access.csv',
            'views/hotel_sequence.xml',
            'views/hotel_report.xml',
            'views/report_hotel_management.xml',
            'views/hotel_view.xml',
            'wizard/hotel_wizard.xml',
    ],
    'css': ['static/src/css/room_kanban.css'],
    'images': ['static/description/Hotel.png'],
    'auto_install': False,
    'installable': True,
    'application': True
}
