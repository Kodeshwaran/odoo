from odoo import models, fields, api, _
from io import BytesIO
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
import base64



class Contract(models.Model):
    _name = 'sale.contract'
    _inherit = 'mail.thread'
    _rec_name = "partner_id"

    contract_date = fields.Datetime('Contract date')
    effective_date = fields.Date('Effective date')
    contract_document = fields.Binary('Contract Document', tracking=True)
    file_name = fields.Char('File Name', tracking=True)
    sale_order_id = fields.Many2one('sale.order')
    partner_id = fields.Many2one('res.partner', string='Customer')
    service_type_id = fields.Many2one('crm.service', string="Service type")
    rims_customer_master_id = fields.Many2one('rims.customer.master')


    def action_generate(self):
        report_content, filename = self.env.ref('sale_costing.contract_sale_order_report')._render_qweb_pdf(self.id)

        if report_content.lstrip().startswith(b'<svg'):
            svg_data = BytesIO(report_content)
            drawing = svg2rlg(svg_data)
            pdf_buffer = BytesIO()
            renderPDF.drawToFile(drawing, pdf_buffer)
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
        else:
            pdf_content = report_content
        file_name = f'Sale Contract-{self.partner_id.name}'

        self.write({
            'contract_document': base64.b64encode(pdf_content),
            'file_name': file_name
        })

class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    service_type_id = fields.Many2one('crm.service', string="Service type")
    epo_costing_ids = fields.One2many('sale.order.line.epo', 'subscription_id', String='EPO', readonly=True,)
    resource_costing_ids = fields.One2many('sale.order.line.resource', 'subscription_id', String='Resource',
                                           readonly=True)

