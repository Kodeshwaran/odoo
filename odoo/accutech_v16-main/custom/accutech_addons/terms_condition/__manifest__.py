# -*- encoding: utf-8 -*-
{
    "name": "Terms & Conditions",
    "version": "13.0",
    "author": "Futurenet Pvt.Ltd.",
    "website": "http://www.futurenet.in",
    "sequence": 0,
    "depends": ['sale','base', 'account', 'purchase', 'product'],
    "category": "All",
    'license': 'LGPL-3',
    "description": """Terms & Conditions""",
    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sale_terms_condition.xml',
        'views/account_terms_condition.xml',
        'views/purchase_terms_condition.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
