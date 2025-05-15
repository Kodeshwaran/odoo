# -*- coding: utf-8 -*-
{
    'name': "Payroll Extended",
    'summary': """This module included addon features for payroll module.""",
    'description': """This module included addon features for payroll module.""",
    'author': "Prabakaran-R/Futurenet Technologies India Pvt Ltd.",
    'website': "http://www.futurenet.in",
    'category': 'Human Resource',
    'version': '15.0.1',
    'images': ['static/src/img/logo.png',],
    'depends': ['base','hr_payroll_community', 'hr', 'hr_extended', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/templates.xml',
        'views/views.xml',
        'views/employee.xml',
        'report/payslip_report.xml',
        'report/payslip_report_view.xml',
        'report/report_mail_sent_status.xml',
        'report/report_mail_sent_status_view.xml',
        'wizards/employee_report_wizard_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
