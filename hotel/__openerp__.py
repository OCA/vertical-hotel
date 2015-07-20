# -*- encoding: utf-8 -*-

{
    "name" : "Hotel Management Base",
    "version" : "1.0",
    "author" : ["Domatix",
                "Serpent Consulting Services Pvt. Ltd.",
                "OpenERP SA" ],
    "category" : "Generic Modules/Hotel Management",
    "depends" : ["sale_stock"],
    "init_xml" : [],
    "demo_xml" : [
    ],
    "data" : [
        "views/hotel_menu_view.xml",
        "views/hotel_amenities_type.xml",
        "views/hotel_services.xml",
        "views/hotel_floor.xml",
        "views/hotel_folio.xml",
        "views/hotel_room_amenities.xml",
        "views/hotel_room_type.xml",
        "views/hotel_room.xml",
        "report/hotel_report.xml",
        "data/hotel_data.xml",
        "data/hotel_folio_workflow.xml",
        "security/hotel_security.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    'installable': True,
    'application': True,
}

