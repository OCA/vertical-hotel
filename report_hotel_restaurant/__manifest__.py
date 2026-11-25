# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Restaurant Management - Reporting",
    "version": "20.0.1.0.0",
    "author": "Odoo Community Association (OCA), Serpent Consulting\
                Services Pvt. Ltd., Odoo S.A.",
    "maintainer": "Serpent Consulting Services Pvt. Ltd.,\
                    Rajan-SerpentCS,\
                    vimalpatelserpentcs",
    "website": "https://github.com/OCA/vertical-hotel",
    "summary": "Restaurant sales analysis: food items, quantities and amounts "
    "by month, category, customer and waiter",
    "depends": ["hotel_restaurant", "report_hotel_reservation"],
    "category": "Services/Hotel",
    "license": "AGPL-3",
    "data": [
        "security/ir.access.csv",
        "views/report_hotel_restaurant_view.xml",
    ],
    "installable": True,
}
