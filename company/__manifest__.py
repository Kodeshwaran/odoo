
{
    'name': 'It company ',
    'version': '1.0.0',
    'sequence':-100,
    'category': 'Company service management',
    'summary': 'Company db management',
    'description': """ """,
    'depends': ['mail','product'],
    'data': [
        'security/ir.model.access.csv',
        'data/employee_tags_data.xml',
        'data/employee.tags.csv',
        'data/sequence_data.xml',
        'data/sequence_meeting_data.xml',
        'wizard/cancel_meeting_views.xml',
        'views/menu.xml',
        'views/employee_views.xml',
        'views/female_employee_views.xml',
        'views/meeting_views.xml',
        'views/employee_tags_views.xml',
        'views/odoo_playground_views.xml',

    ],
    'demo': [    ],
    'application':True,
    'installable': True,
    'auto_install': False,
    'assets': {},
    'license': 'LGPL-3'
}
