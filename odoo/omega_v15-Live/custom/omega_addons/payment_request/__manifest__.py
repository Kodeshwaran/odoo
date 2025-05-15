# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Request',
    'version': '1.1',
    'category': 'Accounts',
    'summary': 'payment request & approval process',
    'description': """
This module for the payment approval process.
    """,
    'depends': ['base', 'account', 'report_xlsx', 'mail','base_accounting_kit','account_check_printing'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/payment_request_sequences.xml',
        'wizard/payment_cheque_report.xml',
        'views/account_move.xml',
        'views/payment_request.xml',
        'views/res_partner_view.xml',
        'wizard/payment_utr_views.xml',
        'wizard/payment_advice_email.xml',
        'wizard/payment_cheque.xml',
        'wizard/payment_request_cancel.xml',
        'report/customer_account_details.xml',
        'data/email_temp_payment_request.xml',
        'report/vendor_payment.xml',
        'report/payment_receipts.xml',

    ],
    'demo': [],
    'installable': True,
    "application": True,
    'auto_install': False,
    'license': 'AGPL-3',
}
