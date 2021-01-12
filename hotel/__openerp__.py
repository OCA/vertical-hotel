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
    "name" : "Hotel Management",
    "version" : "1.0",
    "author" : "Tiny",
    "category" : "Generic Modules/Hotel Management",
    "description": """
    Module for Hotel/Resort/Property management. You can manage:
    * Configure Property
    * Hotel Configuration
    * Check In, Check out
    * Manage Folio
    * Payment

    Different reports are also provided, mainly for hotel statistics.
    """,
    "depends" : ["base","product","sale"],
    "init_xml" : [],
    "demo_xml" : [
    ],
    "update_xml" : [

                    "hotel_view.xml",
                    "hotel_data.xml",
                    "hotel_folio_workflow.xml",
                    "hotel_report.xml",
                    "wizard/hotel_wizard.xml",
                    "security/hotel_security.xml",
                    "security/ir.model.access.csv",

    ],
    "active": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: