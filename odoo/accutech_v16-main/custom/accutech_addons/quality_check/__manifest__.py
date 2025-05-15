# -*- coding: utf-8 -*-
{
    'name': "Quality Check",

    'summary': """
        Manage and track quality checks related to stock operations.""",

    'description': """
        This module provides functionalities for creating and managing quality checks
        for stock picking operations, including tracking quantities passed and failed.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Warehouse',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',  # Define security access rights
        'data/quality_check_sequence.xml',  # Sequence for quality check
        'views/views.xml',  # Tree and form views
        'views/menus.xml',  # Menu structure
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': True,  # Set to True if this module is a standalone application
    'auto_install': False,  # Set to True if you want this module to be auto-installed with its dependencies
}
