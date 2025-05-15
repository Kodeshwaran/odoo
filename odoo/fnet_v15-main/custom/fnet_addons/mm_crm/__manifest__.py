# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'CRM',
    'version': '1.1',
    'category': 'Master',
    'summary': '',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base', 'crm', 'sale_crm', 'sale_management', 'sales_team','voip_community', 'mm_master','sale'],
    'author': 'Futurenet Technologies India Pvt Ltd',
    'data': [
        'security/master_security.xml',
        'security/ir.model.access.csv',
        'views/crm_views.xml',
        'views/sale_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'license': 'AGPL-3',
    'auto_install': False
}
