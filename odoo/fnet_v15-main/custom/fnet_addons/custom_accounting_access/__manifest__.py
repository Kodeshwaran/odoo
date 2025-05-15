{
    'name': 'Custom Accounting Access',
    'version': '15.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Restrict Accounting and Reports menu to a specific user group',
    'author': 'Your Name',
    'depends': ['account', 'hr_contract', 'salary_revision', 'sale_target','sale_target_new'],
    'data': [
        'security/accounting_security.xml',
        'views/account_menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
