# See LICENSE file for full copyright and licensing details.

{
    'name': 'Hotel Reservation Management',
    'version': '12.0.1.0.0',
    'author': 'Odoo Community Association (OCA), Serpent Consulting \
                Services Pvt. Ltd., Odoo S.A.',
    'category': 'Generic Modules/Hotel Reservation',
    'license': 'AGPL-3',
    'summary': 'Manages Guest Reservation & displays Reservation Summary',
    'depends': ['hotel', 'stock', 'mail'],
    'demo': ['data/hotel_reservation_data.xml'],
    'data': [
        'security/ir.model.access.csv',
        'data/hotel_scheduler.xml',
        'data/hotel_reservation_sequence.xml',
        'views/hotel_reservation_view.xml',
        'data/email_template_view.xml',
        'report/checkin_report_template.xml',
        'report/checkout_report_template.xml',
        'report/room_max_report_template.xml',
        'report/hotel_reservation_report_template.xml',
        'report/report_view.xml',
        'views/assets.xml',
        'wizards/hotel_reservation_wizard.xml',
    ],
    'qweb': ['static/src/xml/hotel_room_summary.xml'],
    'installable': True,
    'auto_install': False,
}
