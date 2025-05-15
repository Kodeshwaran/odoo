{
    'name': "sale_target",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mm_master', 'account', 'account_invoice_alert', 'mm_account','subscription_extended'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'wizard/daily_report_views.xml',
        'views/views.xml',
        'views/res_company.xml',
        'views/templates.xml',
        'views/sale_budget.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-
