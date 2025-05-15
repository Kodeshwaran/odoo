{
    'name': 'Fnet Omega CRM Stages',
    'version': '1.0',
    'website': 'https://www.odoo.com/page/crm',

    'depends': ['base','crm','mail'],

    # always loaded
    'data': [    
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'views/document_model.xml',
        'views/unlinkstage.xml',     
      ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}
