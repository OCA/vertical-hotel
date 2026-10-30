# Copyright (C) 2026-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hotel Front Desk Dashboard",
    "version": "20.0.1.0.0",
    "author": "Odoo Community Association (OCA), Serpent Consulting Services Pvt. Ltd.",
    "website": "https://github.com/OCA/vertical-hotel",
    "license": "AGPL-3",
    "category": "Services/Hotel",
    "summary": "Real-time receptionist dashboard: occupancy, arrivals, "
    "departures and room readiness",
    "depends": ["vertical_hotel", "hotel_reservation", "hotel_housekeeping"],
    "data": [
        "security/ir.access.csv",
        "views/hotel_dashboard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hotel_front_desk_dashboard/static/src/scss/hotel_dashboard.scss",
            "hotel_front_desk_dashboard/static/src/js/hotel_dashboard.esm.js",
            "hotel_front_desk_dashboard/static/src/xml/hotel_dashboard.xml",
        ],
    },
    "installable": True,
}
