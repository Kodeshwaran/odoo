# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'VOIP Community',
    'version': '15.0.1',
    'category': 'CRM',
    'summary': '',
    'description': """This module helps salesperson to manage his activities records in a place.""",
    'depends': ['base', 'crm', 'sales_team'],
    'author':'Prabakaran-R/Futurenet Technologies',
    'data': [
        'security/ir.model.access.csv',
        'views/voip_views.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
