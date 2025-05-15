# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from dateutil.relativedelta import relativedelta
import json
import base64
import binascii
import tempfile
from io import StringIO
import os



from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


from odoo.addons import decimal_precision as dp

from werkzeug.urls import url_encode

from collections import defaultdict


class Stage(models.Model):
    _inherit = "crm.stage"

    probability = fields.Float('Probability', group_operator="avg", copy=False)
    restrict_reverse = fields.Boolean('Restrict Reversal', default=False)
    attachment_required = fields.Boolean('Attachment Required', default=False)
    send_alert = fields.Boolean('Send Proposal Submission Alert', default=False)
    is_sales_manager = fields.Boolean(string="Is Sales Manager Validation")
    hide_graph = fields.Boolean(string="Hide in Graph")


class ExpectedClosingLine(models.Model):
    _name = 'expected.closing.line'

    opportunity_id = fields.Many2one('crm.lead')
    date_change = fields.Date(string="Changed on", default=fields.Datetime.now)
    changed_by = fields.Many2one('res.users', string="Changed By", default=lambda self: self.env.user)
    changed_from = fields.Date(string="Changed From")


class CrmLead(models.Model):
    _inherit = "crm.lead"

    value_bl = fields.Float('Value BL')
    budget = fields.Boolean('Budget')
    budget_text = fields.Text()
    authority = fields.Boolean('Authority')
    authority_text = fields.Text()
    need = fields.Boolean('Need')
    need_text = fields.Text()
    time_lead = fields.Boolean('Time')
    time_text = fields.Text()
    sale_type_id = fields.Many2one('sale.type', string="Sale Type")
    sale_sub_type_id = fields.Many2one('sale.type.line', string="Sale Sub Type")
    attachment = fields.Many2many('ir.attachment',string="Quotation Attachment")
    po_attachment = fields.Binary(string='Customer PO Attachment',store=True)
    attachment_filename = fields.Char(string='Filename', store=True)
    expected_closing_track = fields.One2many('expected.closing.line','opportunity_id', string="Expected Closing Date Changes")
    contact_description = fields.Text(string="Contact Description")

    @api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed', 'order_ids.date_order',
                 'order_ids.company_id')
    def _compute_sale_data(self):
        for lead in self:
            total = 0.0
            quotation_cnt = 0
            sale_order_cnt = 0
            company_currency = lead.company_currency or self.env.company.currency_id
            for order in lead.order_ids:
                if order.state in ('draft', 'sent', 'po_receive'):
                    quotation_cnt += 1
                if order.state not in ('draft', 'sent', 'po_receive', 'cancel'):
                    sale_order_cnt += 1
                    total += order.currency_id._convert(
                        order.amount_untaxed, company_currency, order.company_id,
                        order.date_order or fields.Date.today())
            lead.sale_amount_total = total
            lead.quotation_count = quotation_cnt
            lead.sale_order_count = sale_order_cnt

    def action_view_sale_quotation(self):
        res = super(CrmLead, self).action_view_sale_quotation()
        quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent', 'po_receive'))
        res['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent', 'po_receive'])]
        res['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        res['res_id'] = quotations.id
        return res

    @api.onchange('date_deadline')
    def _onchange_date_deadline(self):
        if self._origin.date_deadline:
            vals = {'changed_from': self._origin.date_deadline}
            self.write({'expected_closing_track': [(0, 0, vals)]})

    @api.depends(lambda self: ['stage_id', 'team_id'] + self._pls_get_safe_fields())
    def _compute_probabilities(self):
        lead_probabilities = self._pls_get_naive_bayes_probabilities()
        for lead in self:
            if lead.stage_id.probability:
                lead.probability = lead.stage_id.probability
            elif lead.id in lead_probabilities:
                super(CrmLead, self)._compute_probabilities()

    @api.model
    def create(self, values):
        if self.type == 'opportunity' and values.get('expected_revenue') == 0:
            raise UserError(_('Kindly give Revenue'))
        if self.type == 'opportunity' and values.get('value_bl') == 0:
            raise UserError(_('Kindly give Value BL'))
        return super(CrmLead, self).create(values)

    def action_new_quotation(self):
        quotation = super(CrmLead, self).action_new_quotation()
        quotation['context']['default_sale_type_id'] = self.sale_type_id.id
        if self.sale_sub_type_id:
            quotation['context']['default_sale_sub_type_id'] = self.sale_sub_type_id.id

        return quotation

    def action_set_won(self):
        res = super(CrmLead, self).action_set_won()
        if self.stage_id.is_won and not self.attachment:
            raise ValidationError("Quotation Attachment is required to move to %s stage" % self.stage_id.name)
        if self.stage_id.is_won and self.sale_order_count == 0 and not self.quotation_count > 0:
            raise ValidationError("Please create a quotation before moving to %s stage" % self.stage_id.name)
        if self.stage_id.is_won and self.quotation_count > 0 and self.sale_order_count == 0:
            quotations = self.env['sale.order'].search([('opportunity_id', '=', self.name), ('state', 'in', ['draft', 'sent', 'po_receive'])])
            no_line_quotations = quotations.filtered(lambda x: not x.order_line)
            if no_line_quotations:
                raise ValidationError("Add order lines for quotations or else delete the unwanted quotations")
            line_quotations = quotations.filtered(lambda x: x.order_line)
            for quotation in line_quotations:
                attachment_copy = []
                for att in self.attachment:
                    attachment = att.copy()
                    attachment.write({
                        'res_model': 'sale.order',
                        'res_id': quotation.id,
                        'res_name': quotation.name,
                    })
                    attachment_copy.append(attachment)
                for at in attachment_copy:
                    quotation.write({'attachment': [(4, at.id)]})
                quotation.receive_po()
        return res

    @api.onchange('stage_id')
    def onchange_stage(self):
        values = [self.budget, self.authority, self.need, self.time_lead]
        current_stage = self._origin.stage_id
        if current_stage.probability >= 10:
            if values.count(True) < 3:
                raise ValidationError("Any three of the fields(Budget,Authority,Need, Time) must be checked to move stage")
        if current_stage.restrict_reverse and self.probability < current_stage.probability:
            raise ValidationError("You cant go to previous state after moving the current stage")
        if self.stage_id.is_won and not self.attachment:
            raise ValidationError("Quotation Attachment is required to move to %s stage" % self.stage_id.name)
        if self.stage_id.attachment_required:
            attachments = self.env['ir.attachment'].search_count([('res_model', '=', 'crm.lead'), ('res_id', '=', self.id.origin)])
            if not attachments > 0 and not self.quotation_count > 0 and self.sale_amount_total <= 0:
                raise ValidationError("Attachment is required or quotation must be created to move to %s stage" % self.stage_id.name)
        if self.stage_id.send_alert and self.team_id.user_id:
            for lead in self:
                mail_content = "  Dear  <strong>" + lead.team_id.user_id.name + "</strong>, <br>The Opportunity <strong>" + lead.name + \
                               "</strong> has been submitted for proposal."
                main_content = {
                    'subject': _('Proposal submitted for the Opportunity %s') % lead.name,
                    'email_from': self.env.user.company_id.email,
                    'body_html': mail_content,
                    'email_to': lead.team_id.user_id.partner_id.email
                }
                self.env['mail.mail'].sudo().create(main_content).send()
        if self.stage_id.is_won and self.sale_order_count == 0 and not self.quotation_count > 0:
            raise ValidationError("Please create a quotation before moving to move to %s stage" % self.stage_id.name)
        if self.stage_id.is_won and self.quotation_count > 0 and self.sale_order_count == 0:
            quotations = self.env['sale.order'].search([('opportunity_id', '=', self.name), ('state', 'in', ['draft', 'sent', 'po_receive'])])
            no_line_quotations = quotations.filtered(lambda x: not x.order_line)
            if no_line_quotations:
                raise ValidationError("Add order lines for quotations or else delete the unwanted quotations")
            line_quotations = quotations.filtered(lambda x: x.order_line)
            for quotation in line_quotations:
                attachment_copy = []
                for att in self.attachment:
                    attachment = att.copy()
                    attachment.write({
                        'res_model': 'sale.order',
                        'res_id': quotation.id,
                        'res_name': quotation.name,
                    })
                    attachment_copy.append(attachment)
                for at in attachment_copy:
                    quotation.write({'attachment': [(4, at.id)]})
                quotation.receive_po()
        if self.stage_id and self.stage_id.is_sales_manager and not self.value_bl >= 50000:
            raise UserError(_("This validation is not required as the bottom line value is lower"))


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def unlink(self):
        for rec in self:
            if rec.res_model == 'crm.lead':
                lead = self.env['crm.lead'].search([('id', '=', rec.res_id)])
                if lead and lead.stage_id and lead.stage_id.is_won:
                    raise UserError(_('You cannot delete attachments in %s stage') % lead.stage_id.name)
            if rec.res_model == 'sale.order':
                sale_order = self.env['sale.order'].search([('id', '=', rec.res_id)])
                if sale_order and sale_order.state in ['po_receive','sale','done']:
                    raise UserError(_('You cannot delete attachments in this state'))
        return super(IrAttachment, self).unlink()

    @api.model
    def check(self, mode, values=None):
        """ Restricts the access to an ir.attachment, according to referred mode """
        if self.env.is_superuser():
            return True
        # Always require an internal user (aka, employee) to access to a attachment
        if not (self.env.is_admin() or self.env.user.has_group('base.group_user')):
            raise AccessError(_("Sorry, you are not allowed to access this document."))
        # collect the records to check (by model)
        model_ids = defaultdict(set)  # {model_name: set(ids)}
        if self:
            # DLE P173: `test_01_portal_attachment`
            self.env['ir.attachment'].flush(['res_model', 'res_id', 'create_uid', 'public', 'res_field'])
            self._cr.execute(
                'SELECT res_model, res_id, create_uid, public, res_field FROM ir_attachment WHERE id IN %s',
                [tuple(self.ids)])
            for res_model, res_id, create_uid, public, res_field in self._cr.fetchall():
                if public and mode == 'read':
                    continue
                # if not self.env.is_system() and (res_field or (not res_id and create_uid != self.env.uid)):
                #     raise AccessError(_("Sorry, you are not allowed to access this document."))
                if not (res_model and res_id):
                    continue
                model_ids[res_model].add(res_id)
        if values and values.get('res_model') and values.get('res_id'):
            model_ids[values['res_model']].add(values['res_id'])

        # check access rights on the records
        for res_model, res_ids in model_ids.items():
            # ignore attachments that are not attached to a resource anymore
            # when checking access rights (resource was deleted but attachment
            # was not)
            if res_model not in self.env:
                continue
            if res_model == 'res.users' and len(res_ids) == 1 and self.env.uid == list(res_ids)[0]:
                # by default a user cannot write on itself, despite the list of writeable fields
                # e.g. in the case of a user inserting an image into his image signature
                # we need to bypass this check which would needlessly throw us away
                continue
            records = self.env[res_model].browse(res_ids).exists()
            # For related models, check if we can write to the model, as unlinking
            # and creating attachments can be seen as an update to the model
            access_mode = 'write' if mode in ('create', 'unlink') else mode
            records.check_access_rights(access_mode)
            records.check_access_rule(access_mode)


class VoipPhonecall(models.Model):
    _inherit = "voip.phonecall"

    outcome = fields.Selection([
        ('New Prospect', 'New Prospect'),
        ('Existing Prospect', 'Existing Prospect'),
        ('Suspect', 'Suspect'),
        ('follow', 'Follow-Up'),
        ('nil', 'NIL'),
        ('others', 'Others'),
    ], string='Outcome', default='New Prospect')
    product = fields.Char('Product')
    contact_name = fields.Char('Customer Name')
    value = fields.Float('Value')
    note = fields.Text('Note')
    call_date = fields.Date('Call Date', default=lambda self: fields.Date.today())
    phonecall_type = fields.Selection([
        ('Inside Sale', 'Inside Sale'),
        ('Outside Sale', 'Outside Sale'),
        ('Tender Related', 'Tender Related'),
        ('Proposal', 'Proposal'),
        ('Payment Followup', 'Payment Followup'),
        ('Internal Meeting', 'Internal Meeting'),
        ('Others', 'Others'),
    ], string='Type', default='Outside Sale')
    phonecall_types = fields.Selection([
        ('Inside Sale', 'Inside Sale - New'),
        ('Inside Sales_Existing', 'Inside Sales - Existing'),
        ('Outside Sale', 'Outside Sale - New'),
        ('Outside Sales_Existing', 'Outside Sales - Existing'),
        ('Tender Related', 'Tender Related'),
        ('Proposal', 'Proposal'),
        ('Payment Followup', 'Payment Followup'),
        ('Internal Meeting', 'Internal Meeting'),
        ('Others', 'Others'),
    ], string='Type', default='Outside Sale')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('voip.phonecall') or 'New'
        result = super(VoipPhonecall, self).create(vals)
        return result


class SaleTarget(models.Model):
    _name = "sale.target"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    user_id = fields.Many2one('res.users', string='Sales Person', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    target_line = fields.One2many('sale.target.line', 'target_id', 'Target')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('close', 'Closed'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    def open_target(self):
        from datetime import datetime
        interval = 1
        ds = datetime.strptime(str(self.date_from), '%Y-%m-%d').date()
        print (type(ds), "ADS")
        while ds < self.date_to:
            de = ds + relativedelta(months=interval, days=-1)

            if de > self.date_to:
                de = datetime.strptime(self.date_to, '%Y-%m-%d')

            self.env['sale.target.line'].create({
                'name': ds.strftime('%m/%Y'),
                'code': ds.strftime('%m/%Y'),
                'date_from': ds.strftime('%Y-%m-%d'),
                'date_to': de.strftime('%Y-%m-%d'),
                'target_id': self.id,
            })
            ds = ds + relativedelta(months=interval)
        return self.write({'state':'open'})

    def close_target(self):
        pass


class SaleTargetLine(models.Model):
    _name = "sale.target.line"

    @api.depends('tl_value', 'bl_value')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            amount = 0
            data = self.env['account.move'].search([('invoice_date','>=',line.date_from), ('invoice_date','<=',line.date_to),('type','in',('out_invoice','out_refund')),('state','=','posted')])
            if data:
                for val in data:
                    amount += val.amount_untaxed_signed
            line.update({
                    'achived': amount,
                })

    target_id = fields.Many2one('sale.target', 'Target', ondelete='cascade')
    name = fields.Char(string='Name', readonly=True)
    code = fields.Char(string='Code', readonly=True)
    date_from = fields.Date(string='Date From', required=True, readonly=True)
    date_to = fields.Date(string='Date To', required=True, readonly=True)
    tl_value = fields.Float(string='Top Line')
    bl_value = fields.Float(string='Bottom Line')
    user_id = fields.Many2one('res.users', string='Sales Person', related='target_id.user_id')
    company_id = fields.Many2one('res.company', string='Company', related='target_id.company_id')
    achived = fields.Float(compute='_compute_amount', string='Achived', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('close', 'Closed'),
        ], string='Status', readonly=True, store=True, index=True, tracking=3, related='target_id.state')






