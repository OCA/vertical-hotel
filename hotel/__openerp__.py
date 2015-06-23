# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

{
    "name" : "Hotel Management Base",
    "version" : "1.0",
    "author" : "Tiny,Odoo Community Association (OCA)",
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
    "active": False,
    'installable': True,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
