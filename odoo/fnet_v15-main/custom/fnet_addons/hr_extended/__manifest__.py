# -*- coding: utf-8 -*-
{
    'name': "HR Extended",

    'summary': """To extend the HR Module based on futurenet requirements.""",
    'author': "Futurenet Technologies India Pvt. Ltd./Prabakaran-R",
    'website': "http://www.futurenet.in",
    'category': 'Human Resource',
    'version': '13.0.1',
    'depends': ['base', 'hr', 'hr_contract', 'hr_payroll_community'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'data/cron.xml',
        'views/bank_views.xml',
        'views/employee_views.xml',
        'views/employee_allowance_view.xml',
    ],
    'license': 'AGPL-3',
}
