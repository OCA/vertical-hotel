# See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Reservation Management - Reporting",
    "version": "11.0.1.0.0",
    "author": "Odoo Community Association (OCA),"
    "Serpent Consulting Services Pvt. Ltd., "
    "Odoo S.A.",
    "website": "http://www.serpentcs.com",
    "depends": ["hotel_reservation"],
    "license": "AGPL-3",
    "summary": "State-wise view for hotel reservation "
    "for better business intelligence.",
    "category": "Generic Modules/Hotel Reservation",
    "data": [
        "security/ir.model.access.csv",
        "views/report_hotel_reservation_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
