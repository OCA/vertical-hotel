# -*- encoding: utf-8 -*-

{
    "name" : "Hotel Management Base",
    "version" : "1.0",
    "author" : ["Domatix",
                "Serpent Consulting Services Pvt. Ltd.",
                "OpenERP SA" ],
    "category" : "Generic Modules/Hotel Management",
    "depends" : ["sale"],
    "init_xml" : [],
    "demo_xml" : [
    ],
    "data" : [
        "views/hotel_view.xml",
        "data/hotel_data.xml",
        "data/hotel_folio_workflow.xml",
        "report/hotel_report.xml",
        "wizard/hotel_wizard.xml",
        "security/hotel_security.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    'installable': True,
    'application': True,
}

