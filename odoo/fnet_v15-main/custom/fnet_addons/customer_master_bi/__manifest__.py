# -*- coding: utf-8 -*-
{
    'name': 'Company MASTER',
    'version': '15.0',
    'category': 'TEST',
    'author': 'Futurenet Technologies',    
    'description': """ Customized HRMS module and inherited some fields in following screens
    1. Employee Master
    2. Customer Master
    3. Contract
    4. Payroll
    5. Bulk upload - Trainee details
       """,
    'depends': ['base','sale','account','mail','hr','contacts'],
    'images': [],
    'installable': True,
    'auto_install': False,
    'data' : [
             'security/ir.model.access.csv',
              'views/location_master.xml',
             'views/menu.xml',


              ],
    'qweb': [
            ],

}
