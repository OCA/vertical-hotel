# See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Reservation Management",
    "version": "11.0.1.0.0",
    "author": "Odoo Community Association (OCA),"
    "Serpent Consulting Services Pvt. Ltd., "
    "Odoo S.A.",
    "category": "Generic Modules/Hotel Reservation",
    "license": "AGPL-3",
    "summary": "Manages Guest Reservation and displays Reservation Summary",
    "depends": ["hotel", "stock", "mail"],
    "demo": ["data/hotel_reservation_data.xml"],
    "data": [
        "security/ir.model.access.csv",
        "data/hotel_scheduler.xml",
        "data/hotel_reservation_sequence.xml",
        "templates/email_temp_view.xml",
        "templates/report_checkin.xml",
        "templates/report_checkout.xml",
        "templates/max_room.xml",
        "templates/room_res.xml",
        "templates/room_summ_view.xml",
        "views/hotel_folio.xml",
        "views/hotel_reservation.xml",
        "views/hotel_room.xml",
        "views/quick_room_reservation.xml",
        "views/room_reservation_summary.xml",
        "views/actions.xml",
        "views/menus.xml",
        "wizards/hotel_reservation_wizard.xml",
        "report/hotel_reservation_report.xml",
    ],
    "qweb": ["static/src/xml/hotel_room_summary.xml"],
    "external_dependencies": {"python": ["dateutil"]},
    "installable": True,
    "auto_install": False,
}
