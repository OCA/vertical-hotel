# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    "name" : "Hotel Management Base",
    "version" : "10.0.1.0.0",
    "author" : "Tiny,Odoo Community Association (OCA), Serpent Consulting Services Pvt. Ltd.",
    "category" : "Generic Modules/Hotel Management",
    "description": """
Module for Hotel/Resort/Rooms/Property management. You can manage:

* Configure Property
* Hotel Configuration
* Check In, Check out
* Manage Folio
* Payment

Different reports are also provided, mainly for hotel statistics.
    """,
    "depends" : ["sale"],
    "init_xml" : [],
    "demo_xml" : [
    ],
    "update_xml" : [
                    "hotel_view.xml",
                    "hotel_data.xml",
                    "hotel_folio_workflow.xml",
                    "report/hotel_report.xml",
                    "wizard/hotel_wizard.xml",
                    "security/hotel_security.xml",
                    "security/ir.model.access.csv",
    ],
    'installable': True,
    'application': True,
}
