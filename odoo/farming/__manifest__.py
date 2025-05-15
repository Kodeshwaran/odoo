# -*- coding: utf-8 -*-
{
    'name': 'Farming',
    'version': '15.1',
    'category': 'Invoicing',
    'author': 'Futurenet Technologies',
    'description': """
       """,
    'depends': ['base','account','base_accounting_kit', 'account_standard_report'],
    'installable': True,
    'auto_install': False,
    'data' : [
             'security/ir.model.access.csv',
             'data/account_person_email_corn.xml',
             'views/report_layout.xml',
             'views/account_invoice_inherit.xml',
             'views/account_payment_inherit.xml',
             'wizard/account_invoice_wizard.xml',
             'wizard/inovice_due_report.xml',
              ],
    'qweb': [
            ],

}


































