# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hotel Reservation Management - Reporting",
    "version": "17.0.1.0.0",
    "author": "Odoo Community Association (OCA), Serpent Consulting\
                Services Pvt. Ltd., Odoo S.A.",
    "website": "https://github.com/OCA/vertical-hotel",
    "depends": ["hotel_reservation"],
    "license": "AGPL-3",
    "category": "Generic Modules/Hotel Reservation",
    "data": [
        "security/ir.model.access.csv",
        "views/report_hotel_reservation_view.xml",
    ],
    "installable": True,
}
