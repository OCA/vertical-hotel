# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hotel Website Booking",
    "version": "20.0.1.0.0",
    "author": "Odoo Community Association (OCA), Serpent Consulting Services Pvt. Ltd.",
    "website": "https://github.com/OCA/vertical-hotel",
    "license": "AGPL-3",
    "category": "Services/Hotel",
    "summary": "Hotel website: guests check room type availability and send "
    "reservation requests the front desk confirms",
    "depends": ["website", "portal", "hotel_reservation"],
    "data": [
        "security/ir.access.csv",
        "data/website_menu.xml",
        "data/portal_entry_data.xml",
        "views/hotel_room_views.xml",
        "views/hotel_room_type_views.xml",
        "views/hotel_reservation_views.xml",
        "views/res_config_settings_views.xml",
        "views/website_layout_templates.xml",
        "views/booking_templates.xml",
        "views/homepage_templates.xml",
        "views/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "hotel_website/static/src/scss/hotel_website.scss",
            "hotel_website/static/src/interactions/hotel_booking.esm.js",
        ],
    },
    "installable": True,
    "application": True,
}
