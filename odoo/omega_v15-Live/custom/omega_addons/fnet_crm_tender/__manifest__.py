{
    'name': 'Opportunity To Tender',
    'version': '1.0',
    'category': 'CRM',
    'sequence': 4,
    'summary': 'Opportunity,Tender,Purchase Order,Sale Quotations ',
    'icon': "/fnet_crm/static/img/iswasu.png",
    'description': """

    This application allows to create the tender in opportunity when Won stage.
    Then the relavent tender call the many purchase quotations.
    The sale quots is create on the bid received state in purchase quotation 
    If you select any product in comportable RFQ which is converted the sale quotations remaining 
    RFQ can be changed cancel state
    """,
    'author': 'Futurenet',
    'website': 'http://www.futurenet.in',
    'depends': ['sale','crm','base','sale_crm','purchase_requisition','purchase','account','stock', 'customers_vendors_configuration', 'voip_community', 'mail'],
    'data': [
        'views/account_move.xml',
        'views/approval_config.xml',
        'views/sale_view.xml',
        'views/stock_picking.xml',
        'data/sequences.xml',
        'wizard/approval_status_report_views.xml',
        'wizard/registered_enquiries_report_views.xml',
        'views/oppor_orderline_view.xml',
        'views/purchase_requisition_view.xml',
        'views/purchase_view.xml',
        'views/purchase_config.xml',
        'data/rights_data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/res_partner.xml',
        'views/product_view.xml',
        'views/dsr.xml',
        'views/shipment_mode.xml'
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
