# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Onscreen Reports',
    'version' : '1.1',
    'summary': 'Report',
    'sequence': 15,
    'description': """

    """,
    'category': 'Accounting',
    'website': '',
    'images' : [ ],
    'depends' : ['account', 'base', 'apex_einvoice', 'mm_account'],
    'data': [
        'views/paper_format.xml',
        'views/menu.xml',
        'views/assets.xml',
        # 'report/account_invoice_report_view.xml',
        # 'report/account_move_report_view.xml',
        'report/sale_quote.xml',
        'report/bank_check_view.xml',
        'report/journal_voucher.xml',
        'report/dc_report_view.xml',
        'report/payment_advise.xml',
        'report/tax_invoice.xml',
        'report/tax_invoice_view.xml',

    ],
    'demo': [
    ],
    'qweb': [
       
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'mm_onscreen_report/static/src/css/company_css.css'
        ]
    },
    'license': 'AGPL-3',

}
