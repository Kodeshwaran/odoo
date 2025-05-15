# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Omega Costing Calculation',
    'version': '1.0',
    'category': 'Customer Relationship Management',
    'sequence': 2,
    'summary': 'Oppotunity inherits',
    'description': """
                Submission Date added,
                Product Line items added,
                convert to calls for BID,
                   """,
    'author': 'Futurenet',
    'website': 'http://www.futurenet.in/',
    'depends': ['base', 'crm', 'sale_stock', 'purchase_requisition', 'purchase', 'fnet_omega_multi_rfq', 'stock', 'account'],
    'data': [      
        'security/ir.model.access.csv',
        'wizard/duty_amount_update_view.xml',
        'views/purchase_inherit_view.xml',
        'views/costing_view.xml',
        'views/purchase_rfq_inherit_view.xml',
       
        #~ 'security/mline_security.xml',
            ],
    'demo': [
       
            ],
    'test': [
       
            ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
