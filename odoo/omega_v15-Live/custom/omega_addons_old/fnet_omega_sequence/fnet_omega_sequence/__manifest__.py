{
    'name': 'Opportunity To Tender sequence',
    'version': '1.0',
    
    'sequence': 5,
    
    'icon': "/fnet_crm/static/img/iswasu.png",
    'description': """

    This application cotains the sequences for the Opportunity to Tender module.
    
    """,
    'author': 'Iswasu Technologies',
    'website': 'http://www.futurenet.in',
    'depends': ['sale','crm','base','sale_crm','purchase_requisition','purchase',],
    'data': [
        
        'views/oppor_sequence.xml',
        'views/purchase_order_sequence.xml',
        'views/sale_order_sequence.xml',
        'views/sale_amendment_sequence.xml',
       
            ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
