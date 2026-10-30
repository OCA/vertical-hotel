# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hotel Reservation Management - Reporting",
    "version": "20.0.1.0.0",
    "author": "Odoo Community Association (OCA), Serpent Consulting\
                Services Pvt. Ltd., Odoo S.A.",
    "website": "https://github.com/OCA/vertical-hotel",
    "summary": "Reservation analysis: room nights and guests by month, "
    "room type and state",
    "depends": ["hotel_reservation"],
    "license": "AGPL-3",
    "category": "Services/Hotel",
    "data": [
        "security/ir.access.csv",
        "views/report_hotel_reservation_view.xml",
    ],
    "installable": True,
}
