# -*- coding: utf-8 -*-

{
    'name': 'Final Settlement & Gratuity',
    'version': '13.0',
    'category': 'HR',
    'summary': 'HR Management',
    'description': """
                    final settlement,
                    gratuity,
                    """,
    'author': 'APPSGATE FZC LLC',
    'website': 'http://www.apps-gate.net',

    'images':[
        'static/src/img/main-screenshot.png'
    ],

    'depends': ['base' , 'hr', 'hr_payroll_community', 'hr_contract', 'hr_extended', 'hr_contract_types'],
    'data': [
                'security/ir.model.access.csv',
                'security/security.xml',
                'views/exit_interview.xml',
                'views/no_due.xml',
                'views/final_settlement_view.xml',
                'views/final_settlement_type_master.xml',
                'reports/settlement_report.xml',
                'reports/settlement_report_template.xml',
    
    ],
    'license': 'AGPL-3',
    'price':'20',
    'currency':'USD',
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
