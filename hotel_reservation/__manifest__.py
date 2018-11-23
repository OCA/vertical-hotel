# See LICENSE file for full copyright and licensing details.

{
    'name': 'Hotel Reservation Management',
    'version': '11.0.1.0.0',
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
        'views/hotel_reservation_sequence.xml',
        'views/hotel_reservation_view.xml',
        'views/email_temp_view.xml',
        'views/report_checkin.xml',
        'views/report_checkout.xml',
        'views/max_room.xml',
        'views/room_res.xml',
        'views/room_summ_view.xml',
        'wizards/hotel_reservation_wizard.xml',
        'report/hotel_reservation_report.xml',
    ],
    'qweb': ['static/src/xml/hotel_room_summary.xml'],
    'installable': True,
    'auto_install': False,
}
