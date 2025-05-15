# -*- coding: utf-8 -*-
{
    'name': "Time Off Extended",
    'summary': """This module extend the features of Time Off module.""",
    'description': """Includes validations and additional fields in time off forms.""",
    'author': "Futurenet Technologies/Prabakaran-R",
    'website': "http://www.futurenet.in",
    'category': 'Uncategorized',
    'version': '13.0.1',
    'depends': ['base', 'hr_holidays', 'hr_extended', 'hr', 'resource', 'website', 'contacts', 'employee_confirmation'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron_views.xml',
        'views/hr_holidays_views.xml',
        'views/views.xml',
    ],
}
