# -*- coding: utf-8 -*-
{
    'name': "custom_sales_report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Sasidharan.K",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sale_extended','sale_approval_kanak', 'product', 'sale_revision_history', 'web', 'account_reports'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/report_sale_order_paperformat.xml',
        'data/report_paperformat.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/sale_order_temp.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
