# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Restaurant Management - Reporting",
    "version": "17.0.1.0.0",
    "author": "Odoo Community Association (OCA), Serpent Consulting\
                Services Pvt. Ltd., Odoo S.A.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.,\
                    Rajan-SerpentCS,\
                    vimalpatelserpentcs",
    "website": "https://github.com/OCA/vertical-hotel",
    "depends": ["hotel_restaurant", "report_hotel_reservation"],
    "category": "Generic Modules/Hotel Restaurant",
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/report_hotel_restaurant_view.xml",
    ],
    "installable": True,
}
