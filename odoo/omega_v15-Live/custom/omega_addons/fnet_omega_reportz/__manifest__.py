{
    'name': 'Futurenet Covering Letter',
    'version': '1.0',
    'category': 'Reports',
    'sequence': 2,
    'author': 'Futurenet',
    'icon': "/fnet_report/static/img/icon.png",
    'description':
		"""
		This Application contain five reports and create fields required for reports,They are
		   1.Sale Quotation Covering Letter
		""",
    'depends': [ 'base','sale','account','purchase', 'stock', 'fnet_crm_tender', 'base_accounting_kit', 'account_invoice_pro_forma_sequence'],
   
    'data': [
			'views/invoice_views.xml',
			# 'views/sale_order_view.xml',
			# 'report/layouts.xml',
			'report/report_covering_letter.xml',
			'report/report_covering_letter_view.xml',
			'report/report_quotation.xml',
			'report/report_quotation_view.xml',
			'report/report_order_confirmation.xml',
			'report/report_order_confirmation_view.xml',
			'report/report_purchase_order.xml',
			'report/report_purchase_order_view.xml',
			'report/report_rfq.xml',
			'report/report_rfq_view.xml',
			'report/report_invoice.xml',
			'report/report_invoice_view.xml',
			'report/report_invoice_without_head.xml',
			'report/report_invoice_without_head_view.xml',
			'report/report_rcm_invoice .xml',
			'report/report_rcm_invoice_view.xml',
			'report/report_profoma_invoice.xml',
			'report/report_proforma_invoice_view.xml',
			'report/report_shipment_order.xml',
			'report/report_shipment_order_view.xml',
			'report/report_shipment_order_without_head.xml',
			'report/report_shipment_order_without_head_view.xml',
			'report/report_shipment_order_pack.xml',
			'report/report_shipment_order_pack_view.xml',
			'report/report_shipment_order_pack_without_head.xml',
			'report/report_shipment_order_pack_without_head_view.xml',
                        ],
  
    'installable': True,
    'application': True,
    'auto_install': False,

    
}
