{
    'name': 'Accounting Customization',
    'version': '10.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary':
    'Accounting customization',
    'author': 'Iswasu Technologies',
    'icon': "/journal_reports/static/img/icon.png",
    'depends': ['web','account'],
    
    'data': [
        'report/cheque_payment_report.xml',
        'report/journal_voucher_report.xml',
  
        ],
        
    'installable': True,
    'auto_install': False,
    'application': True,
}
