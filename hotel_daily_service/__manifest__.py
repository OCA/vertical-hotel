# See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Daily Service",
    "version": "11.0.1.0.0",
    "author": "Odoo Community Association (OCA)," "Coop IT Easy SCRLfs",
    "website": "https://github.com/OCA/vertical-hotel",
    "license": "AGPL-3",
    "summary": "Facilitates adding Daily Services to Hotel Folio.",
    "category": "Generic Modules/Hotel Housekeeping",
    "external_dependencies": {"python": ["dateutil"]},
    "depends": ["hotel"],
    "data": [
        "data/hotel_daily_service_data.xml",
        "wizard/hotel_daily_service_wizard.xml",
        "views/hotel_folio.xml",
    ],
    "installable": True,
}
