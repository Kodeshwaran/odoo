# -*- coding: utf-8 -*-
#################################################################################
# Author      : Kanak Infosystems LLP. (<https://www.kanakinfosystems.com/>)
# Copyright(c): 2012-Present Kanak Infosystems LLP.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.kanakinfosystems.com/license>
#################################################################################
{
    "name": "Sale Approval Rules",
    "summary": "Sale Approval Rules",
    'images': ['static/description/banner.jpg'],
    "description": "Sale Approval Rules",
    'summary': 'Sale Order Approval Rules',
    "version": "13.0.1.1",
    "category": "Sales",
    "license": "OPL-1",
    "author": "Kanak Infosystems LLP.",
    "website": "https://www.kanakinfosystems.com",
    "depends": ["hr", "sale_management", 'sale_extended', 'mail'],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "wizard/create_product_view.xml",
        "views/approval_config.xml",
        "views/sale_order_config.xml",
        "views/sale_view.xml",
        "wizard/custom_warning_view.xml"
    ],
    'sequence': 1,
    "installable": True,
    "price": 30,
    "currency": "EUR",
    'live_test_url': 'https://youtu.be/J9nTXPpmxaM',
}

