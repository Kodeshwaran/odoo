{
    'name': 'Narration Filter',
    'version': '15.0.1',
    'category': 'General',
    'summary': 'This module enables narration field to be searchable in sales and accounting.',
    'sequence': 1,
    'description': """This module enables narration field to be searchable in sales and accounting.""",
    'depends': ['account', 'sale'],
    'data': [
        "views/move_views.xml",
        "views/sale_views.xml",
    ],
    'installable': True
}