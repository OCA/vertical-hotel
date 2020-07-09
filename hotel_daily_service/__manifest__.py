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
    "demo": ["demo/hotel_daily_service_demo.xml"],
    "data": [
        "wizard/hotel_daily_service_wizard.xml",
        "wizard/hotel_service_daily_report_wizard.xml",
        "reports/hotel_service_daily_report.xml",
        "views/hotel_folio.xml",
        "views/menus.xml",
    ],
    "installable": True,
}
