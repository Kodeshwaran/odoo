# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Purchase',
    'version': '1.1',
    'category': 'Master',
    'summary': '',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base', 'purchase', 'sale', 'stock', 'employee_confirmation', 'partner_creation', 'mm_master'],
    'author':'Pearl',
    'data': [
        'security/master_security.xml',
        'security/ir.model.access.csv',
        'wizard/stock_picking_views_wizard.xml',
        'wizard/po_expected_delivery_views.xml',
        'views/purchase_views.xml',
        'views/stock_picking_views.xml',
        'report/delivery_challan_report.xml',
        'report/goods_return_note_report.xml',
        'report/purchase_order_report.xml',
        'report/report_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'license': 'AGPL-3',
    'auto_install': False
}
