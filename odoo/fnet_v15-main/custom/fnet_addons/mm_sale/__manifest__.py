# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'CRM',
    'version': '1.1',
    'category': 'Master',
    'summary': '',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base', 'sales_team', 'sale', 'mail', 'contacts', 'board', 'crm', 'account', 'l10n_in_sale',],
    'author':'Pearl',
    'data': [
        'security/master_security.xml',
        'security/ir.model.access.csv',
        'wizard/delivery_date_update_views.xml',
        'wizard/late_delivery_alert_views.xml',
        'wizard/sale_po_views.xml',
        # 'views/sale_dashboard.xml',
        'views/sale_views.xml',
        'views/templates.xml',
        'data/email_delivery_date_update.xml',
        'data/sequence.xml',
        'reports/report.xml',
        'reports/report_pdf.xml',
        'reports/pro_forma_invoice.xml',
        'reports/pro_forma_invoice_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'license': 'AGPL-3',
    'auto_install': False
}
