# -*- coding: utf-8 -*-
{
    'name': "Purchase Extended",

    'summary': """
        Custom module extending the functionality of the purchase module.""",

    'description': """
        This module adds extended features for purchase orders, including combining RFQs into a single RFQ and customizations related to purchasing processes.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in the module listing
    'category': 'Purchases',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'purchase',
        'sale',
        'sale_purchase',
        'sale_extended',
        'product'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_views.xml',  # Your custom views
        'data/sequences.xml',  # Sequence file for combined RFQs
        'data/server_actions.xml',  # Server actions if applicable
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
