# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Balance Confirmation Letter',
    'version': '1.1',
    'category': 'Master',
    'summary': '',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base', 'account', 'l10n_in',],
    'author':'Pearl',
    'data': [
        # 'security/master_security.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'wizard/balance_sheet_views.xml',
        'views/res_config.xml',
        'reports/balance_letter_template.xml',
        'reports/balance_letter_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False
}
