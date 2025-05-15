{
    'name': 'Fnet Omega Crm Inherit',
    'version': '1.0',
    'website': 'https://www.odoo.com/page/crm',

    'depends': ['crm','mail','purchase','fnet_omega_crm','purchase_requisition'],

    # always loaded
    'data': [

        'view.xml',
        #~ 'lead_view.xml',
        'purchase_order_line_view.xml',
        #~ 'crm_inherit_view.xml',
        'account_invoice_view.xml',
        'views/sale_view.xml',
        'views/purchase_view.xml',
        'wizard/create_multiple_quotation_view.xml'
        #~ 'security/ir.model.access.csv',

      ],
    #~ 'qweb': [
        #~ 'static/src/xml/todo_action.xml',
    #~ ],
    # only loaded in demonstration mode

    'installable': True,
    'auto_install': False,
    'application': True,
}
