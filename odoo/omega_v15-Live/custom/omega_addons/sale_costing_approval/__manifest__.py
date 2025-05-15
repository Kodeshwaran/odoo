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
    "name": "Sale Costing Approval Rules",
    "summary": "Sale Costing Approval Rules",
    'images': ['static/description/banner.jpg'],
    "description": "Sale Costing Approval Rules",
    'summary': 'Sale Costing Approval Rules',
    "version": "13.0.1.1",
    "category": "Sales",
    "license": "OPL-1",
    "author": "Futurenet Technologies India Pvt Ltd.",
    "website": "https://www.futurenet.in",
    "depends": ["hr", "sale_management", 'sale_costing'],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "views/approval_config.xml",
        "views/sale_order_config.xml",
        "views/sale_view.xml",
        "wizard/custom_warning_view.xml"
    ],
    'sequence': 1,
    "installable": True,
    "price": 30,
    "currency": "EUR",
}
