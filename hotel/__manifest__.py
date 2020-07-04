# See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Management",
    "version": "11.0.1.0.0",
    "author": "Odoo Community Association (OCA),"
    "Serpent Consulting Services Pvt. Ltd., "
    "Odoo S.A.",
    "category": "Hotel Management",
    "website": "https://github.com/OCA/vertical-hotel/",
    "depends": ["sale_stock", "point_of_sale"],
    "license": "AGPL-3",
    "summary": "Hotel Management to Manage Folio and Hotel Configuration",
    "demo": ["data/hotel_data.xml"],
    "data": [
        "security/hotel_security.xml",
        "security/ir.model.access.csv",
        "data/hotel_sequence.xml",
        "data/paperformat.xml",
        "report/hotel_report.xml",
        "report/report_hotel_management.xml",
        "views/hotel_folio.xml",
        "views/hotel_room.xml",
        "views/hotel_room_amenities.xml",
        "views/hotel_room_type.xml",
        "views/hotel_service_type.xml",
        "views/hotel_services.xml",
        "views/product_product.xml",
        "views/res_company.xml",
        "views/actions.xml",
        "views/menus.xml",
        "wizard/hotel_wizard.xml",
    ],
    "css": ["static/src/css/room_kanban.css"],
    "images": ["static/description/Hotel.png"],
    "auto_install": False,
    "installable": True,
    "application": True,
}
