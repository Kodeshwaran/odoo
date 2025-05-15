# -*- coding: utf-8 -*-
{
    'name': "Sale Costing",
    'summary': """This module helps to calculate sale price from the purchase agreement.""",
    'author': "Futurenet Technologies/Prabakaran-R",
    'website': "http://www.futurenet.in",
    'category': 'Sales',
    'version': '13.0.1',
    'depends': ['product', 'purchase_requisition', 'sale', 'fnet_crm_tender'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/datas.xml',
        'data/sequence.xml',
        'views/configuration_views.xml',
        'views/sale_costing_views.xml',
        'views/purchase_views.xml',
        'views/sale_views.xml',
    ],
}
