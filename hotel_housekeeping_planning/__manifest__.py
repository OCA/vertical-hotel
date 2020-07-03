# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


{
    "name": "Hotel Housekeeping Planning",
    "version": "11.0.1.0.0",
    "author": "Odoo Community Association (OCA)," "Coop IT Easy SCRLfs",
    "category": "Hotel Management",
    "website": "https://github.com/OCA/vertical-hotel/",
    "depends": ["hotel_housekeeping", "hotel_reservation"],
    "data": [
        "reports/housekeeping_planning.xml",
        "reports/reports.xml",
        "views/hotel_reservation.xml",
    ],
    "license": "AGPL-3",
    "summary": "Generates a planning for room housekeeping.",
    "images": ["static/description/Hotel.png"],
    "installable": True,
}
