
{
    'name': 'menu_name',
    'version': '15.1',
    'category': 'account',
    'summary': 'menu name',
    'description': """ This module will change the menu and action name for payment as receipts and vendor credit note as credit note""",
    'depends': [
        'account', 'product',
    ],
    'data': [
         'views/menu_name.xml',
            ],
}
