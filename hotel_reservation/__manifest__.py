# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hotel Reservation Management",
    "version": "17.0.1.0.0",
    """author": "Odoo Community Association (OCA),
               Serpent Consulting Services Pvt. Ltd.,
               Odoo S.A"""
    "category": "Generic Modules/Hotel Reservation",
    "license": "AGPL-3",
    "summary": "Manages Guest Reservation & displays Reservation Summary",
    "website": "https://github.com/OCA/vertical-hotel",
    "depends": ["hotel", "stock", "mail", "website_sale"],
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
    "external_dependencies": {"python": ["dateutil"]},
    "installable": True,
}
