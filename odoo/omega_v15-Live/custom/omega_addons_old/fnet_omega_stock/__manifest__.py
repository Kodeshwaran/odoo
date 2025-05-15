# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Inventory Management',
    'version': '1.1',
    'summary': 'Inventory, Logistics, Warehousing',
    'description': """
Manage multi-warehouses, multi- and structured stock locations
==============================================================

The warehouse and inventory management is based on a hierarchical location structure, from warehouses to storage bins.
The double entry inventory system allows you to manage customers, vendors as well as manufacturing inventories.

Odoo has the capacity to manage lots and serial numbers ensuring compliance with the traceability requirements imposed by the majority of industries.

Key Features
------------
* Moves history and planning,
* Minimum stock rules
* Support for barcodes
* Rapid detection of mistakes through double entry system
* Traceability (Serial Numbers, Packages, ...)

Dashboard / Reports for Inventory Management will include:
----------------------------------------------------------
* Incoming Products (Graph)
* Outgoing Products (Graph)
* Procurement in Exception
* Inventory Analysis
* Last Product Inventories
* Moves Analysis
    """,
    'website': 'https://www.odoo.com/page/warehouse',
    'depends': ['product', 'procurement', 'barcodes', 'web_planner'],
    'category': 'Warehouse',
    'sequence': 13,
    'depends': ['stock'],
    'data': [
        'views/stock_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
