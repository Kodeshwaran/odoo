# -*- coding: utf-8 -*-
{
    'name': "subscription_extended",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_subscription', 'crm', 'sale', 'mail', 'product', 'account', 'mm_master', 'mm_account','hr','hr_payroll_community', 'sales_team', 'default_invoice_terms', 'partner_creation'],

    # always loaded
    'data': [
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/sale_subscription.xml',
        'views/templates.xml',
        'views/subscription_product.xml',
        'views/contract_configuration.xml',
        'views/warranty_product.xml',
        'reports/report.xml',
        'reports/report_pdf.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'AGPL-3',
}
