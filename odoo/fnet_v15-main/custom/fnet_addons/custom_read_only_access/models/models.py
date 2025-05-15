# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
from lxml import etree


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(ResPartner, self).create(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartner, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == 'form':
            if self.env.user.has_group('custom_read_only_access.group_read_only'):
                doc = etree.XML(res['arch'])
                for field in res['fields']:
                    for node in doc.xpath("//field[@name='%s']" % field):
                        node.set("readonly", "1")
                        modifiers = json.loads(node.get("modifiers"))
                        modifiers['readonly'] = True
                        node.set("modifiers", json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc)
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(AccountMove, self).create(vals)

    def write(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(AccountMove, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMove, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == 'form':
            if self.env.user.has_group('custom_read_only_access.group_read_only'):
                doc = etree.XML(res['arch'])
                for field in res['fields']:
                    for node in doc.xpath("//field[@name='%s']" % field):
                        node.set("readonly", "1")
                        modifiers = json.loads(node.get("modifiers"))
                        modifiers['readonly'] = True
                        node.set("modifiers", json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc)
        return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def create(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(AccountPayment, self).create(vals)

    def write(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(AccountPayment, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountPayment, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == 'form':
            if self.env.user.has_group('custom_read_only_access.group_read_only'):
                doc = etree.XML(res['arch'])
                for field in res['fields']:
                    for node in doc.xpath("//field[@name='%s']" % field):
                        node.set("readonly", "1")
                        modifiers = json.loads(node.get("modifiers"))
                        modifiers['readonly'] = True
                        node.set("modifiers", json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc)
        return res


class AccountEInvoice(models.Model):
    _inherit = 'account.einvoice'

    @api.model
    def create(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(AccountEInvoice, self).create(vals)

    def write(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(AccountEInvoice, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountEInvoice, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == 'form':
            if self.env.user.has_group('custom_read_only_access.group_read_only'):
                doc = etree.XML(res['arch'])
                for field in res['fields']:
                    for node in doc.xpath("//field[@name='%s']" % field):
                        node.set("readonly", "1")
                        modifiers = json.loads(node.get("modifiers"))
                        modifiers['readonly'] = True
                        node.set("modifiers", json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc)
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(SaleOrder, self).create(vals)

    def write(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(SaleOrder, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == 'form':
            user = self.env['res.users'].search([('id', '=', self.env.context.get('uid', False))])
            if self.env.user.has_group('custom_read_only_access.group_read_only'):
                doc = etree.XML(res['arch'])
                for field in res['fields']:
                    for node in doc.xpath("//field[@name='%s']" % field):
                        node.set("readonly", "1")
                        modifiers = json.loads(node.get("modifiers"))
                        modifiers['readonly'] = True
                        node.set("modifiers", json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc)
        return res

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(PurchaseOrder, self).create(vals)

    def write(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(PurchaseOrder, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PurchaseOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == 'form':
            user = self.env['res.users'].search([('id', '=', self.env.context.get('uid', False))])
            if self.env.user.has_group('custom_read_only_access.group_read_only'):
                doc = etree.XML(res['arch'])
                for field in res['fields']:
                    for node in doc.xpath("//field[@name='%s']" % field):
                        node.set("readonly", "1")
                        modifiers = json.loads(node.get("modifiers"))
                        modifiers['readonly'] = True
                        node.set("modifiers", json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc)
        return res

class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    @api.model
    def create(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(SaleSubscription, self).create(vals)

    def write(self, vals):
        if self.env.user.has_group('custom_read_only_access.group_read_only'):
            raise ValidationError("You are a Read Only User. You are not allowed to perform this operation.")
        return super(SaleSubscription, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleSubscription, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == 'form':
            user = self.env['res.users'].search([('id', '=', self.env.context.get('uid', False))])
            if self.env.user.has_group('custom_read_only_access.group_read_only'):
                doc = etree.XML(res['arch'])
                for field in res['fields']:
                    for node in doc.xpath("//field[@name='%s']" % field):
                        node.set("readonly", "1")
                        modifiers = json.loads(node.get("modifiers"))
                        modifiers['readonly'] = True
                        node.set("modifiers", json.dumps(modifiers))
                    res['arch'] = etree.tostring(doc)
        return res