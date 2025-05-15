# -*- coding: utf-8 -*-
{
    'name': "employee_confirmation",

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
    'depends': ['base', 'hr', 'mail', 'portal', 'mm_master'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/probation_wizard.xml',
        'data/cron.xml',
        'views/res_config_settings.xml',
        'views/employee.xml',
        'views/template.xml',
        'views/probation_review.xml',
        'report/confirmation_report_view.xml',
        'report/confirmation_report.xml',
        'report/probation_extension_view.xml',
        'report/probation_extension.xml',
        'report/internship_extend_report.xml',
        'report/internship_extend_report_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
