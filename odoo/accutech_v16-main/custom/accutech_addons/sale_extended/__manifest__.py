# -*- coding: utf-8 -*-
{
    'name': "Sale Extended",
    'summary': """This module for sale extend fields and other changes""",
    'author': "Futurenet Technologies/Sasidharan-K",
    'website': "http://www.futurenet.in",
    'category': 'Sales extended',
    'version': '16.0.1',
    'depends': [
        'base',
        'sale',
        'purchase',
        'sale_purchase',
        'stock',
        'sale_stock',
        'sales_team',
        'account',
        'product',
        'uom'
    ],
    'data': [
        'data/groups.xml',
        'security/ir.model.access.csv',
        'wizard/sale_po_views.xml',
        'views/sale_views.xml',
        'views/product_stock.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_extended/static/src/js/description_short_scroll.js',  # Include the JavaScript file
            'sale_extended/static/src/css/scrollable_field.css',        # Include the CSS file (optional)
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
