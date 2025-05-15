# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Master',
    'version': '1.1',
    'category': 'Master',
    'summary': '',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','crm','sales_team','account', 'l10n_in'],
    'author':'Pearl',
    'data': [
        'security/master_security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/product_views.xml',
        'views/master_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'license': 'AGPL-3',
    'auto_install': False
}
