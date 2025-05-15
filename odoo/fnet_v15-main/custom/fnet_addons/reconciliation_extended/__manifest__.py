
{
    'name': 'reconciliation_extended',
    'version': '1.2',
    'summary': 'reconciliation_extended',
    'sequence': 10,
    'description': """""",
    'category': 'Accounting/Accounting',
    'website': 'https://www.odoo.com/app/invoicing',
    'depends': ['base', 'account', 'payment_request'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/reconcilliation.xml',
        'wizard/reconcilliation_wizard.xml',
    ],
    'qweb': [
        'static/src/xml/reconciliation_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'reconciliation_extended/static/src/js/reconcilliation.js',
        ],
    },

    'license': 'LGPL-3',
}
