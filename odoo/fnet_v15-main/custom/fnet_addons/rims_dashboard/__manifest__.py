# -*- coding: utf-8 -*-
{
    'name': "Rims Dashboard",
    'icon': 'static/description/icon.png',

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Kevin Nelthropp",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website', 'web', 'sale_subscription', 'mail'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/sequence.xml',
        'views/rims_links.xml',
        'views/configuration.xml',
        'views/customer_master.xml',
        'views/rims_dashboard.xml',
        'views/epo_change_request.xml',
        'views/mt_change_request.xml',
        'views/res_config_settings.xml',
        'wizard/customer_report.xml',
        'wizard/contract_report.xml',

    ],

    'images': ["static/description/icon.png"],

    'assets': {
        'web.assets_backend': [
            'rims_dashboard/static/src/css/dashboard.css',
            'rims_dashboard/static/src/css/style.css',
            'rims_dashboard/static/src/js/rims_dashboard.js',
        ],
        'web.assets_qweb': [
            'rims_dashboard/static/src/xml/**/*',
        ],
    }
}
