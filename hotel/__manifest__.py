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
    'name' : 'Hotel Management Base',
    'version' : '10.0.1.0.0',
    'author' : 'Tiny, Odoo Community Association (OCA), Serpent Consulting Services Pvt. Ltd.',
    'category' : "Generic Modules/Hotel Management",
    'license' : "AGPL-3",
    'description' : '''
Module for Hotel/Resort/Rooms/Property management. You can manage:

* Configure Property
* Hotel Configuration
* Check In, Check out
* Manage Folio
* Payment

Different reports are also provided, mainly for hotel statistics.
    ''',
    'depends' : ['sale', 'sale_stock', 'point_of_sale', 'report'],
    'init_xml' : [],
    'demo': ['views/hotel_data.xml'],
    'data': [
            'security/hotel_security.xml',
            'security/ir.model.access.csv',
            'views/hotel_sequence.xml',
            'views/hotel_report.xml',
            'views/report_hotel_management.xml',
            'views/hotel_view.xml',
            'wizard/hotel_wizard.xml',
    ],
    'css': ['static/src/css/room_kanban.css'],
    'auto_install' : False,
    'installable' : True,
    'application' : True,
    'active' : False
}
