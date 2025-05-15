# -*- coding: utf-8 -*-
{
    'name': 'PRODUCT MASTER',
    'version': '15.0',
    'category': 'TEST',
    'author': 'Futurenet Technologies',
    'depends': ['base','sale','account','mail','hr','contacts'],
    'images': [],
    'installable': True,
    'auto_install': False,
    'data' : [
             'security/ir.model.access.csv',
              'views/product_master.xml',
             'views/menu.xml',


              ],
    'qweb': [
            ],

}
