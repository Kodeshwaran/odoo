# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Wizard Report',
    'version': '1.1',
    'category': 'HR',
    'summary': 'HR Module',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['crm','base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/dsr_view.xml',
        'wizard/dsr_view.xml',
        'wizard/opportunity_view.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
    'auto_install': False
}
