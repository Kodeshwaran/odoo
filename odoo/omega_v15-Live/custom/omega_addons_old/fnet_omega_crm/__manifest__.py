{
    'name': 'Opportunity To Tender',
    'version': '1.0',
    'category': 'CRM',
    'sequence': 4,
    'summary': 'Opportunity,Tender,Purchase Order,Sale Quotations ',
    'icon': "/fnet_omega_crm/static/img/icon.png",
    'description': """

    This application allows to create the tender in opportunity when Won stage.
    Then the relavent tender call the many purchase quotations.
    The sale quots is create on the bid received state in purchase quotation 
    If you select any product in comportable RFQ which is converted the sale quotations remaining 
    RFQ can be changed cancel state
    """,
    'author': 'Iswasu',
    'website': 'http://www.futurenet.in',
    'depends': ['sale','stock','crm','base','sale_crm','purchase_requisition','purchase','fnet_omega_crm_stage','account'],
    'data': [
        'views/sale_view.xml',
        'views/sale_order_sequence.xml',
        'views/oppor_orderline_view.xml',
        'views/oppor_sequence.xml',
        'data/rights_data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/product_view.xml',
        'views/sale_team_view.xml',  
        'wizard/budget.xml',
        'report/report_budget.xml',
        'views/sale_inherit.xml',
        'views/Business Vertical_demo.xml',
        'views/rfq_report_changes.xml',
        'views/lead_changes.xml',        
        'views/stock_move_view.xml',      
        'views/res_partner_view.xml',      
        #~ 'views/sale_config_setting_view.xml',    
            ],

    'qweb': [
        "static/xml/sales_team_dashboard.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
