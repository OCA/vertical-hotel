# See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Tourist Tax",
    "version": "11.0.1.0.0",
    "author": "Odoo Community Association (OCA)," "Coop IT Easy SCRLfs",
    "website": "https://github.com/OCA/vertical-hotel",
    "license": "AGPL-3",
    "summary": "Adds Tourist Tax to Hotel Folio.",
    "category": "Generic Modules/Hotel",
    "depends": ["hotel"],
    "data": [
        "security/ir.model.access.csv",
        "data/hotel_service_type.xml",
        "views/hotel_tourist_tax.xml",
    ],
    "installable": True,
}
