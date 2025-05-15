{
    'name': 'Picking Operations Report',
    'version': '1.0',
    'category': 'Warehouse',
    'depends': ['base', 'stock'],
    'data': [
        'data/paperformat.xml',
        'views/stock_picking.xml',  # Paper format definition
        'views/report_action.xml',  # Paper format definition
        'data/picking_server.xml',
        'views/report_picking_operations.xml',
    ],
    'installable': True,
    'application': False,
}

