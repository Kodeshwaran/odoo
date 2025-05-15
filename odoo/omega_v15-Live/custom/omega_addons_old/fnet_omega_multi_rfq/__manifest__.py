# -*- coding: utf-8 -*-
{
    'name': "Fnet Omega Multiple RFQ",

    'summary': """
       Multiple RFQ """,

    'description': """
       Creating Muliple RFQ from Tender
    """,

    'author': "Futurenet",
    'website': "http://www.futurenet.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'CRM',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'purchase_requisition'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
