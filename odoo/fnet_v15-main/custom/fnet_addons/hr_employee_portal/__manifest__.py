# -*- coding: utf-8 -*-
{
    'name': "Self Employee",
    'icon': 'static/description/icon.png',

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Haari C.",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_contract', 'hr_payroll_community', 'hr_holidays', 'hr_payroll_extended', 'hr_leave_cancel', 'hr_resignation', 'employee_confirmation', 'mm_master'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'data/data.xml',
        'views/views.xml',
        # 'views/server_act_views.xml',
    ],

    'images': ["static/description/icon.png"],
}
