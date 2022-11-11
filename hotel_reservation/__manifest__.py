# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hotel Reservation Management",
    "version": "15.0.1.0.0",
    "author": "Odoo Community Association (OCA), Serpent Consulting \
                Services Pvt. Ltd., Odoo S.A.",
    "category": "Generic Modules/Hotel Reservation",
    "license": "AGPL-3",
    "summary": "Manages Guest Reservation & displays Reservation Summary",
    "website": "https://github.com/OCA/vertical-hotel",
    "depends": ["hotel", "stock", "mail"],
    "demo": ["data/hotel_reservation_data.xml"],
    "data": [
        "security/ir.model.access.csv",
        "data/hotel_scheduler.xml",
        "data/hotel_reservation_sequence.xml",
        "data/email_template_view.xml",
        "views/hotel_reservation_view.xml",
        "report/checkin_report_template.xml",
        "report/checkout_report_template.xml",
        "report/room_max_report_template.xml",
        "report/hotel_reservation_report_template.xml",
        "report/report_view.xml",
        "wizards/hotel_reservation_wizard.xml",
    ],
    "assets": {
        "web.assets_qweb": [
            "hotel_reservation/static/src/xml/hotel_room_summary.xml",
        ],
        "web.assets_backend": [
            "hotel_reservation/static/src/css/room_summary.css",
            "hotel_reservation/static/src/js/hotel_room_summary.js",
        ],
    },
    "external_dependencies": {"python": ["dateutil"]},
    "installable": True,
}
