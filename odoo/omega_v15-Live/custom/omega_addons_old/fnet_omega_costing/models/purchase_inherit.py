# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError,except_orm


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    history_line = fields.One2many('history.order.line', 'purchase_history_id', 'History', readonly=True)
    costing_line = fields.One2many('purchase.costing.line', 'purchase_costing_id', 'Costing')
    product_line = fields.One2many('purchase.product.line', 'purchase_product_id', 'Product')
    cost_history_line = fields.One2many('cost.history.line', 'purchase_cost_history_id', 'Cost History')
    currency_cost_id = fields.Many2one('res.currency', 'Currency')
    currency_cost_id = fields.Many2one('res.currency', 'Currency')
    exchange_rate = fields.Float('Exchange Rate')
    lead_id = fields.Many2one('crm.lead', 'Enquiry', readonly=True)
    contact_name = fields.Char('Contact Name', size=64)
    function = fields.Char('Function', size=64)
    title_id = fields.Many2one('res.partner.title', 'Title')
    cnf_amount = fields.Float('CNF', readonly=True)
    duty_amount = fields.Float('Duty', readonly=True)
    cost_amount = fields.Float('Cost', digits_compute= dp.get_precision('Cost') ,readonly=True, default=1.00)
    duty_id = fields.Many2one('costing.duty', 'Duty')
    margins = fields.Float( 'Margin')
    note_document = fields.Html('Documents')
    subject = fields.Html('Subject')
    signature = fields.Html('Signature')
    delivery_period = fields.Char('Delivery Period')
    delivery_term = fields.Char('Delivery Terms')
    shipping_method = fields.Char('Shipping Method')
    vendor_payment_term = fields.Char('Payment Term')
    validity = fields.Integer('Validity')
    offer = fields.Float('Offer',digits=(16, 0), readonly = True, default=1)
    #~ margin_amt=fields.Float( 'Margin')
    cost_status = fields.Selection([('draft', 'Load Currency'),
                                   ('progress', 'Progress'),
                                   ('convertion', 'Convertion'),
                                   ('margin', 'Margin'),
                                   ('done', 'Done')],'Status', default='draft')
    #~ duty_exempted=fields.Boolean('Duty Exempted', default=True)
    #~ is_merged_po=fields.Boolean('Merged PO', default=False)
    user_id = fields.Many2one(related='lead_id.user_id',relation='res.users', string='Responsible',store=True)
    state = fields.Selection([
        ('draft', 'Draft PO'),
        ('sent', 'RFQ Sent'),
        ('bid received','Bid Received'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    def bid_received(self):
        self.write({'state': 'bid received'})

    def send_rfq(self):
        self.write({'state':'sent'})

    def button_approve(self, force=False):
        #~ val = self.env['ir.sequence'].next_by_code('confirm.purchase')
        #~ re=self.write({'name':val})
        req_id = self.env['purchase.requisition'].search([('id', '=', self.requisition_id.id)])
        if req_id:
           if not req_id.quote_count:
              raise UserError(_('Please select the sale quotes in Purchase Agreements..!'))
           else:
              return super(PurchaseOrder, self).button_approve(force=True)

        return super(PurchaseOrder, self).button_approve(force=True)

    def button_confirm(self):
        for order in self:
            val = order.env['ir.sequence'].next_by_code('purchase.confirm')
            order.name = val
            if order.state not in ['draft', 'sent', 'bid received']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step':
                order.button_approve(force=True)
            else:
                order.write({'state': 'to approve'})
        return True

    def load_currency(self):
        if self.state in ['draft','sent']:
           raise except_orm('Messages', 'Please change the state to bid received!')
        copy_of_cost = []
        self.write({'currency_cost_id': self.currency_id.id, 'exchange_rate': self.currency_id.rate})
        self.env.cr.execute("SELECT id FROM purchase_costing WHERE active='true'")
        line_list = [i[0] for i in self.env.cr.fetchall()]
        line = [li for li in self.costing_line]
        for cost in line_list:
            if not line:
                vals = {'purchase_costing_id': self.id, 'costing_id': cost}
                cost_cr = self.env['purchase.costing.line'].create(vals)
                copy_of_cost.append(cost_cr)
            else:
                for copy1 in copy_of_cost:
                    obj = self.env['purchase.costing.line'].browse(copy1)
                    obj.write({'purchase_costing_id': line.id, 'costing_id': line.costing_id.id})
        for product_line in self.order_line:
            vals = {'purchase_product_id': self.id,
                    'purchase_line_id': product_line.id,
                    'product_id': product_line.product_id.id,
                    'product_qty': product_line.product_qty,
                    'ot_unit_price': product_line.price_unit,
                    'ot_total_price': product_line.price_subtotal,
                    'item_no': product_line.item_no,
                    'margin_amt': product_line.margin_amt
                    }
            self.env['purchase.product.line'].create(vals)
        return self.write({'cost_status': 'progress'})

    def calculate_conversion(self):
        total = []
        freight_total = []
        if self.amount_total > 0.00:
            if self.state != 'done':
                total += [prod_line.ot_total_price for prod_line in self.product_line]
                freight_total += [prod_line.freight_price for prod_line in self.product_line]
                fr_sr = self.env['purchase.costing'].search([('name', '=', 'Freight')])
                fr = self.env['purchase.costing.line'].search(
                    [('purchase_costing_id', '=', self.id), ('costing_id', '=', fr_sr.id)])
                fr.write({'amount': sum(freight_total)})
                duty_amt = [cost_line.amount for cost_line in self.costing_line if cost_line.duty_applicable is True]
                duty = (sum(duty_amt) + sum(total)) * self.duty_id.amount
                cnf_amt = [cost_line.amount for cost_line in self.costing_line]
                cnf = sum(cnf_amt) + duty + sum(total)
                cost = cnf / sum(total)
                self.write({'duty_amount': duty, 'cnf_amount': cnf, 'cost_amount': cost})
        else:
            raise UserError(
                _("Error! You can not Calculating this process. Only for confirm. Because Product price is Zero"))
        return True

    def cal_confirm(self):
        return self.write({'cost_status': 'convertion'})

    def draft(self):
        prod_obj = self.env['purchase.product.line']
        cost_obj = self.env['purchase.costing.line']
        prod = [prod_line.id for prod_line in self.product_line]
        cost = [cost_line.id for cost_line in self.costing_line]
        for val in prod:
            obj = prod_obj.browse(val)
            obj.unlink()
        #~ cost_obj.unlink(cr, uid, cost, context=context)
        self.write({'cnf_amount': 0.00, 'duty_amount': 0.00, 'cost_amount':0.00})
        return self.write({'cost_status': 'draft'})

    def gen_process(self):
        freight_total1 = []
        for prod_line in self.product_line:
            ot_unit_price_margin = (prod_line.ot_unit_price * prod_line.margin_amt/100.0) + prod_line.ot_unit_price
            freight_total1 = [prod_line.freight_price]
            ot_tot_price = prod_line.ot_unit_price * prod_line.product_qty
            aed_total = (prod_line.ot_unit_price * prod_line.product_qty) + sum(freight_total1)
            aed_total = (aed_total * self.cost_amount * self.exchange_rate)
            aed_total = (aed_total * prod_line.margin_amt/100.0) + aed_total
            aed_unit = aed_total / prod_line.product_qty
            prod_line.write({'ot_total_price': ot_tot_price,'ot_unit_price': prod_line.ot_unit_price,'unit_price':aed_unit, 'total_price':aed_total}),
            margin = (aed_unit * prod_line.margin_amt/100.0) + aed_unit
            margin_total = (margin * prod_line.product_qty)
            prod_line.write({'margin': aed_unit, 'margin_price': aed_total+prod_line.margin_price})
            self.write({'cnf_amount': aed_unit})
        return True

    def _prepare_history_product_line(self,margin, prod, prod_line):
        res = {
              'history_product_id': prod.id,
              'product_id': prod_line.product_id.id,
              'product_qty': prod_line.product_qty,
              'ot_unit_price': prod_line.ot_unit_price,
              'ot_total_price': prod_line.ot_total_price,
              'unit_price': prod_line.unit_price,
              'total_price': prod_line.total_price,
              'margins': margin,
              'margin': prod_line.margin,
              'margin_price': prod_line.margin_price,
              'item_no': prod_line.item_no,
              'margin_amt': prod_line.margin_amt
              }
        return res

    def done(self):
        vals = {
            'purchase_cost_history_id':self.id,
            'offer':'OFFER ' + str(int(self.offer)),
            'currency_cost_id':self.currency_cost_id.id,
            'exchange_rate':self.exchange_rate,
            'cnf_amount':self.cnf_amount,
            'duty_amount':self.duty_amount,
            'cost_amount':self.cost_amount,
            'duty_id':self.duty_id.id,
            'margins':self.margins,
               }
        prod = self.env['cost.history.line'].create(vals)
        for prod_line in self.product_line:
            prod_vals = self._prepare_history_product_line(self.margins,  prod, prod_line)
            self.env['history.product.line'].create(prod_vals)
            so_vals = {'tender_id':self.requisition_id.id,'purchase_id':self.id, 'partner_id':self.partner_id.id, 'offer':'OFFER ' + str(int(self.offer)), 'ot_unit_price':prod_line.ot_unit_price, 'purchase_line_id':prod_line.purchase_line_id.id}
            pr_sr = self.env['request.so.line'].search([('product_id', '=', prod_line.product_id.id), ('purchase_id', '=', self.id)])
            old_pr = [sale.id for sale in self.env['request.so.line'].browse(pr_sr.ids) if sale.unit_price == prod_line.unit_price]
            if old_pr:
                for val in old_pr:
                    obj=self.env['request.so.line'].browse(val)
                    obj.unlink()
            call_so = self.env['request.so.line'].create(so_vals)
            call_so.write(self._prepare_history_product_line(self.margins, prod, prod_line))
        for cost_line in self.costing_line:
            cost_vals = {
                     'history_costing_id':prod.id,
                     'costing_id':cost_line.costing_id.id,
                     'amount':cost_line.amount,
                     'duty_applicable':cost_line.duty_applicable,

                        }
            self.env['history.costing.line'].create(cost_vals)
        self.offer += 1
        return self.write({'cost_status':'done'})

# purchase_order_inherit()


class HistoryOrderLine(models.Model):
    _name = 'history.order.line'

    purchase_history_id = fields.Many2one('purchase.order', 'History', readonly=True)
    product_id = fields.Many2one('product.product', 'Product')
    name = fields.Char('Description', size=64)
    uom_id = fields.Many2one('product.uom', 'Unit of Measure')
    product_qty = fields.Char('Quantity')
    item_no = fields.Char('Item No')
    margin_amt = fields.Float('Margin')

# history_order_line()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    request_id = fields.Many2one('purchase.requisition', 'Call for bid')
    item_no = fields.Char('Item No')
    margin_amt = fields.Float('Margin')

# purchase_order_line_inherit()


class PurchaseCostingLine(models.Model):
    _name = 'purchase.costing.line'

    purchase_costing_id = fields.Many2one('purchase.order', 'Purchase')
    costing_id = fields.Many2one('purchase.costing', 'Charges')
    amount = fields.Float('In Amount')
    duty_applicable = fields.Boolean('Duty Applicable')
    item_no = fields.Char('Item No')
    margin_amt = fields.Float( 'Margin')
    percentage = fields.Float("In Percentage")

    @api.onchange('amount', 'percentage')
    def onchange_amount(self):
        if self.percentage:
            self.amount = (sum(self.purchase_costing_id.product_line.mapped('ot_total_price')) * (self.percentage/100))


class PurchaseProductLine(models.Model):
    _name = 'purchase.product.line'

    purchase_product_id = fields.Many2one('purchase.order', 'Purchase')
    purchase_line_id = fields.Many2one('purchase.order.line', 'Purchase Line')
    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float('Quantity')
    margin_amt = fields.Float("Margin")
    ot_unit_price = fields.Float('Unit Price')
    ot_total_price = fields.Float('Total Price')
    unit_price = fields.Float('AED Unit Price')
    total_price = fields.Float('AED Total Price')
    margin = fields.Float('Unit Sale Price')
    freight_price = fields.Float('Freight Charges')
    margin_price = fields.Float('Customer Price')
    item_no = fields.Char('Item No')
    margin_amt = fields.Float( 'Margin')


class CostHistoryLine(models.Model):
    _name = 'cost.history.line'

    purchase_cost_history_id = fields.Many2one('purchase.order', 'Purchase')
    offer = fields.Char('Offer', size=64, readonly=True)
    currency_cost_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    exchange_rate = fields.Float('Exchange Rate', readonly=True)
    cnf_amount = fields.Float('CNF', readonly=True)
    duty_amount = fields.Float('Duty', readonly=True)
    cost_amount = fields.Float('Cost', digits_compute= dp.get_precision('Cost') ,readonly=True)
    duty_id = fields.Many2one('costing.duty', 'Duty', readonly=True)
    tab_costing_line = fields.One2many('history.costing.line', 'history_costing_id', 'Costing' ,readonly=True)
    tab_product_line = fields.One2many('history.product.line', 'history_product_id', 'Product' ,readonly=True)
    item_no = fields.Char('Item No')
    margin_amt = fields.Float('Margin')

# cost_history_line()

class HistoryCostingLine(models.Model):
    _name = 'history.costing.line'

    history_costing_id = fields.Many2one('cost.history.line', 'Cost History')
    costing_id = fields.Many2one('purchase.costing', 'Charges')
    amount = fields.Float('Amount')
    duty_applicable = fields.Boolean('Duty Applicable')
    item_no = fields.Char('Item No')
    margin_amt = fields.Float('Margin')

class HistoryProductLine(models.Model):
    _name = 'history.product.line'

    history_product_id = fields.Many2one('cost.history.line', 'Product History')
    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float('Quantity')
    ot_unit_price = fields.Float('Unit Price')
    ot_total_price = fields.Float('Total Price')
    unit_price = fields.Float('AED Unit Price')
    total_price = fields.Float('AED Total Price')
    margin = fields.Float('Unit Sale Price')
    margin_price = fields.Float('Customer Price')
    item_no = fields.Char('Item No')
    margin_amt = fields.Float('Margin')

# history_product_line()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    request_id = fields.Many2one('purchase.requisition', 'Call for bid')

# stock_picking()


class AccountMove(models.Model):
    _inherit = 'account.move'

    request_id = fields.Many2one('purchase.requisition', 'Call for bid')

# account_invoice()

