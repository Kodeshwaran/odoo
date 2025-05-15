# -*- coding: utf-8 -*-
{
    'name': "Customers Vendors Configuration",
    'summary': """Configure the customer and vendors.""",
    'description': """Includes all the requirement in Dome Project.""",
    'author': "Futurenet Technologies",
    'website': "http://www.futurenet.in",
    'category': 'All',
    'version': '13.0.1',
    'depends': ['base', 'sale', 'purchase', 'account', 'product'],
    'data': [
        'views/views.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
