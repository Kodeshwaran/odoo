# -*- coding: utf-8 -*-
{
    'name': 'HR Late Arrival Management',

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'hr_attendance_geolocation', 'hr_holidays_extended', 'hr_attendance_extended'],

    'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'data/hr_attendance.xml',
        'views/hr_attendance.xml',
        # 'wizard/cond_approve.xml',
    ],
}
