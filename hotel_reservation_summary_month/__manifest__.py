# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Hotel Reservation Month Summary",
    "version": "11.0.1.0.0",
    "author": "Odoo Community Association (OCA), Coop IT Easy SCRLfs",
    "category": "Hotel Management",
    "website": "https://github.com/OCA/vertical-hotel/",
    "depends": ["hotel_reservation_summary_base"],
    "data": ["views/room_reservation_summary.xml"],
    "license": "AGPL-3",
    "summary": "Generates a monthly summary view of reservations.",
    "images": ["static/description/Hotel.png"],
    "installable": True,
}
