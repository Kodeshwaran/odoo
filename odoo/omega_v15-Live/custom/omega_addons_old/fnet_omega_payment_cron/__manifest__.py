{
    'name': 'Payment Cron',
    'version': '1.2',
    'author': 'Omega',
    'category': 'Invoice',
    'sequence': 8,
    'depends': [
        'base_setup',
        'analytic',
        'mail',
        'account'
    ],
    'data': [
    'views/views.xml',   
    ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}
