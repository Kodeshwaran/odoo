from odoo import models, fields, api, _

class ProformaInvoice(models.Model):
    _name = 'proforma.invoice'
    _description = 'Proforma Invoice'
    _inherit = ['mail.thread']

    proforma_name = fields.Char(string="Proforma Reference", default=lambda self: _('New'))
    sale_order_id = fields.Many2one('sale.order', string="Sale Order", readonly=True)
    proforma_percentage = fields.Float(string="Proforma Percentage", readonly=True)
    line_ids = fields.One2many('proforma.invoice.line', 'proforma_id', string="Invoice Lines")
    total_amount = fields.Float(string="Total Amount", compute="_compute_total_amount", store=True)
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user')
    activity_ids = fields.One2many(
        'mail.activity', 'res_id', 'Activities',
        auto_join=True,
        groups="base.group_user", )
    message_ids = fields.One2many(
        'mail.message', 'res_id', string='Messages',
        domain=lambda self: [('message_type', '!=', 'user_notification')], auto_join=True)
    amount_untaxed = fields.Float(string="Untaxed Amount", compute="_compute_total_amount", store=True)
    amount_tax = fields.Float(string="Tax", compute="_compute_total_amount", store=True)

    @api.depends('line_ids.subtotal', 'line_ids.tax_ids', 'line_ids.quantity', 'line_ids.unit_price')
    def _compute_total_amount(self):
        for record in self:
            untaxed = 0.0
            tax_total = 0.0
            for line in record.line_ids:
                line_subtotal = line.quantity * line.unit_price
                taxes = line.tax_ids.compute_all(line.unit_price, quantity=line.quantity)
                untaxed += line_subtotal
                tax_total += sum(t['amount'] for t in taxes.get('taxes', []))
            record.amount_untaxed = untaxed
            record.amount_tax = tax_total
            record.total_amount = untaxed + tax_total

    def amount_total_in_words(self):
        """
        Converts the total amount into words in title case and appends the Abu Dhabi currency (AED) with Fils.
        """
        try:
            # dirhams = int(self.amount_total)
            # fils = round((self.amount_total - dirhams) * 100)
            #
            # dirhams_words = num2words(dirhams, lang='en').title()
            #
            # fils_words = num2words(fils, lang='en').title() if fils > 0 else None
            #
            # if fils_words:
            #     return f"USD {dirhams_words}, And {fils_words} Fils Only"
            # else:
            #     return f"USD {dirhams_words} Only"
            amount_in_words = self.currency_id.amount_to_text(self.total_amount).replace(',', '')
            return amount_in_words

        except Exception as e:
            return f"Error converting amount to words: {e}"

    @api.depends('line_ids.subtotal')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(line.subtotal for line in record.line_ids)

    @api.model
    def create(self, vals):
        if 'proforma_name' not in vals:
            sequence = self.env['ir.sequence'].search([('code', '=', 'proforma.sale.invoice')], limit=1)
            if sequence:
                vals['proforma_name'] = sequence.next_by_id()
            else:
                vals['proforma_name'] = _('New')
        return super(ProformaInvoice, self).create(vals)

    def action_send_proforma_email(self):
        template = self.env.ref('proforma_invoice.mail_template_proforma_invoice')
        if template:
            for record in self:
                template.send_mail(record.id, force_send=True)

    def amount_total_in_words(self):
        try:
            amount_in_words = self.sale_order_id.currency_id.amount_to_text(self.total_amount).replace(',', '')
            return amount_in_words

        except Exception as e:
            return f"Error converting amount to words: {e}"


class ProformaInvoiceLine(models.Model):
    _name = 'proforma.invoice.line'
    _description = 'Proforma Invoice Line'

    proforma_id = fields.Many2one('proforma.invoice', string="Proforma Invoice")
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Unit Price")
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)
    item_no = fields.Char(string="Item Number", readonly=True, default="New")
    product_name = fields.Char(string="Product Name", readonly=True, default="New")
    tax_ids = fields.Many2many('account.tax', string="Taxes")

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
