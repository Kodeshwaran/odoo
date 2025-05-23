# -*- coding: utf-8 -*-
{
    'name': "SALESPERSON DETAIL DASHBOARD",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'sale','sales_team','account','purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'view.xml',
        'pipeline_payment_view.xml',
        'lead_aging_view.xml',
        'record_rule.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
