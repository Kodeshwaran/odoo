# -*- coding: utf-8 -*-
{
    'name': "Hr Resignation",

    'summary': 'Employee Resignation Management',

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HR',
    'version': '13.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'AG_final_settlement', 'resource', 'hr_holidays'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/cron.xml',
        'data/email_template.xml',
        'views/views.xml',
        'views/templates.xml',
        'wizard/resignation_wizard_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
