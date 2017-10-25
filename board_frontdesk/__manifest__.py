# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{

    'name': 'Board for Hotel FrontDesk',
    'version': '10.0.1.0.0',
    'author': 'Odoo Community Association (OCA), Serpent Consulting\
                Services Pvt. Ltd., ODOO S.A.',
    'category': 'Board/Hotel FrontDesk',
    'license': 'AGPL-3',
    'website': 'http://www.serpentcs.com',
    'depends': ['board',
                'report_hotel_reservation',
                'report_hotel_restaurant'
                ],
    'data': ['views/board_frontdesk_view.xml'],
    'description': '''
                This module implements a dashboard for hotel FrontDesk that
                includes:
                    * Calendar view of Today's Check-In and Check-Out For
                      Hotel Reservation
                    * Calendar view of Weekly Check-In and Check-Out For Hotel
                      Reservation
                    * Calendar view of Monthly Check-In and Check-Out For
                      Hotel Reservation
                    * View of Room Reservation Summary and Quick Reservation
                    * Real-Time Updates on Room Availability
                    * A collaborative information regarding Today's Restaurant
                      Orders and Currently Reserved Tables Details
    ''',
    'installable': True,
}
