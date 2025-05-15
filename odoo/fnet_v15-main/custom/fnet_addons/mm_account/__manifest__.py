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
    'depends': ['base','account', 'sale','mm_master', 'mm_purchase'],
    'author':'Pearl',
    'data': [
        'security/master_security.xml',
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/sale_type_views.xml',
        'wizard/update_commitment.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
