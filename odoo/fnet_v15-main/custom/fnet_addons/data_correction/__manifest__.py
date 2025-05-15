# -*- coding: utf-8 -*-
{
    'name': "Data Correction",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Prabakaran-R/Futurenet Technologies",
    'website': "http://www.futurenet.in",
    'category': 'General',
    'version': '15.0.1',
    'depends': ['base', 'sale', 'purchase', 'account', 'crm', 'stock', 'apex_einvoice'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/updation_fields.xml',
    ],
}
