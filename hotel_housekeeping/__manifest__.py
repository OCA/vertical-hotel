# See LICENSE file for full copyright and licensing details.

{
    'name': 'Hotel Housekeeping Management',
    'version': '11.0.1.0.0',
    'author': 'Odoo Community Association (OCA), Serpent Consulting \
               Services Pvt. Ltd., Odoo S.A.',
    'website': 'https://github.com/OCA/vertical-hotel',
    'license': 'AGPL-3',
    'summary': 'Manages Housekeeping Activities and its Process',
    'category': 'Generic Modules/Hotel Housekeeping',
    'depends': ['hotel'],
    'demo': ['views/hotel_housekeeping_data.xml'],
    'data': [
        'security/ir.model.access.csv',
        'views/report_hotel_housekeeping.xml',
        'views/hotel_housekeeping_view.xml',
        'report/hotel_housekeeping_report.xml',
        'wizard/hotel_housekeeping_wizard.xml',
    ],
    'installable': True,
}
