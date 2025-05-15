# -*- coding: utf-8 -*-
{
    'name': "Salary Revision",

    'summary': """
        Update salary and salary history management in contracts""",

    'description': """
        To manage employee salary history and salary revision process  
    """,

    'author': "Futurenet Technologies India Pvt Ltd/P.Padmajothi",
    'website': "http://www.futurenet.in",
    'installable': True,
    'application': True,
    'auto_install': False,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resource',
    'version': '15.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_contract', 'hr_payroll_community', 'hr_extended'],
    'web_icon': "salary_revision,static/description/icon.ico",

    # always loaded
    'data': [
        'wizard/salary_revision.xml',
        'security/ir.model.access.csv',
        # 'views/templates.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}