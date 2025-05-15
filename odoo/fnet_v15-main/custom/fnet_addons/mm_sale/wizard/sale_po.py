# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang


class SalePo(models.TransientModel):
    _name = "sale.po"
    _description = 'Sale Po'

    partner_id = fields.Many2one('res.partner', string="Vendor", required=True)
    sale_id = fields.Many2one('sale.order', "Sale")
    sale_line = fields.One2many('sale.po.line', 'sale_po_id', 'Sale')

    @api.model
    def default_get(self, fields):
        res = super(SalePo, self).default_get(fields)
        sale = self.env['sale.order'].browse(self.env.context.get('active_id'))
        res['sale_id'] = sale.id
        lines = []
        for line in sale.order_line:
            line_dict = {}
            line_dict['product_id'] = line.product_id.id
            line_dict['qty'] = line.product_uom_qty
            line_dict['sale_line_id'] = line.id
            line_dict['sale_po_id'] = self.id
            line_dict['product_uom'] = line.product_uom.id
            lines.append((0, 0, line_dict))
        res['sale_line'] = lines
        return res

    def create_po(self):
        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)))
        val = {'partner_id':self.partner_id.id,
        'sale_id':self.sale_id.id,
        'name':self.env['ir.sequence'].next_by_code('purchase.order', sequence_date=seq_date)
        }
        pur = self.env['purchase.order'].create(val)
        for line in self.sale_line:
            if line.select_line == True:
                val_line = {
                'name':line.sale_line_id.name,
                'order_id':pur.id,
                'product_id':line.sale_line_id.product_id.id,
                'sale_line_id':line.sale_line_id.id,
                'product_qty':line.qty,
                'product_uom':line.sale_line_id.product_uom.id,
                'date_planned':datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'price_unit':1.0,
                'display_type':False
                }
                self.env['purchase.order.line'].create(val_line)
        domain = [('sale_id', '=', self.sale_id.id)]
        return {
            'name': _('Purchase'),
            'domain': domain,
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="o_view_nocontent_smiling_face">
                        Documents are attached to the tasks of your project.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your project.
                    </p>'''),
            'limit': 80,
            'context': "{'default_sale_id': %d}" % (self.sale_id.id)
        }

class SalePoLine(models.TransientModel):
    _name = "sale.po.line"
    _description = 'Sale Po'

    sale_po_id = fields.Many2one('sale.po', 'Sale Po')
    select_line = fields.Boolean('Select')
    sale_line_id = fields.Many2one('sale.order.line', "Sale")
    product_id = fields.Many2one('product.product', 'Product')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    qty = fields.Float('Quantity')
