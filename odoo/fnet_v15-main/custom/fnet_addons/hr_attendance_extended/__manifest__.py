# -*- coding: utf-8 -*-
{
    'name': "hr_attendance_extended",

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
    'depends': ['base', 'hr_attendance', 'hr', 'hr_extended'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/res_config_settings.xml',
        'views/attendance.xml',
        'views/work_location.xml',
        'views/hr_employee.xml',
        'wizard/attendance_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
