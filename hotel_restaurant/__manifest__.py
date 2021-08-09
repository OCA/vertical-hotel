# See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Restaurant Management",
    "version": "14.0.1.0.0",
    "author": "Odoo Community Association (OCA), Serpent Consulting\
                Services Pvt. Ltd., Odoo S.A.",
    "category": "Generic Modules/Hotel Restaurant",
    "website": "https://github.com/OCA/vertical-hotel",
    "depends": ["hotel", "point_of_sale"],
    "license": "AGPL-3",
    "summary": "Table booking facilities and Managing customers orders",
    "demo": ["views/hotel_restaurant_data.xml"],
    "data": [
        "security/ir.model.access.csv",
        "report/hotel_restaurant_report.xml",
        "views/res_table.xml",
        "views/kot.xml",
        "views/bill.xml",
        "views/folio_order_report.xml",
        "views/hotel_restaurant_sequence.xml",
        "views/hotel_restaurant_view.xml",
        "wizard/hotel_restaurant_wizard.xml",
    ],
    "installable": True,
}
