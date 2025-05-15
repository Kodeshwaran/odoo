# -*- coding: utf-8 -*-
{
    'name': "Employee Documents",
    'summary': """Employee enrollment """,
    'description': """This module for the employee enroll.""",
    'author': "Muthaiyan-S/Futurenet Technologies",
    'website': "http://www.futurenet.in",
    'category': 'Employee',
    'version': '15.0.1',
    'depends': ['website', 'base', 'mail', 'hr_recruitment', 'hr', 'hr_extended', 'hr_recruitment_survey', 'mm_master'],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'data/template_view.xml',
        'wizard/create_registration_view.xml',
        'wizard/offer_letter.xml',
        'views/ref_config_settings.xml',
        'views/hr_applicant.xml',
        'views/recruitment.xml',
        'views/hr_employee.xml',
        'views/employee_registration.xml',
        'reports/regular_employee_template.xml',
        'reports/offer_letter_pdf.xml',
    ],
    'license': 'AGPL-3',
    'assets': {
        'web.assets_frontend': [
            'employee_documents/static/src/js/front_end.js',
            'employee_documents/static/src/css/style.css',
        ],

    },
    'installable': True,
    "application": True,
    'auto_install': False,
}
