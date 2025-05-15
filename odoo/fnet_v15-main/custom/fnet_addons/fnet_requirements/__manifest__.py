# -*- coding: utf-8 -*-
{
    'name': "Futurenet Requirements",
    'summary': """This module includes some features in Odoo.""",
    'description': """This module includes some features in Odoo.""",
    'author': "Prabakaran-R/Futurenet Technologies",
    'website': "http://www.futurenet.in",
    'category': 'All',
    'version': '13.0.1',
    'depends': ['web','account', 'sale', 'product', 'stock', 'mm_account', 'mm_crm', 'mm_master', 'mm_onscreen_report', 'mm_purchase', 'mm_sale', 'mm_wizard_report', 'subscription_extended', 'access_restriction_by_ip', 'account_standard_report', 'bank_reconciliation', 'hr_attendance_geolocation', 'hr_payroll_community', 'web_responsive', 'account_reports'],
    'data': [
        'views/views.xml',
        'security/security.xml'
    ],
    'license': 'AGPL-3',
}
