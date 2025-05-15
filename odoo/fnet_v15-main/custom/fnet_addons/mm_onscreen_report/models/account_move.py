#-*- coding:utf-8 -*-

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'


    def get_tax_amt(self, obj, amount):
        amt = obj.currency_id.amount_to_text(amount)
        return amt


    def get_tax_des(self, obj):
        self.env.cr.execute('''
        SELECT hsn, price_subtotal, SUM(cgst_val) AS cgst_val, SUM(sgst_val) AS sgst_val, SUM(igst_val) AS igst_val,
        COALESCE(ROUND(SUM(cgst),2), '0') AS cgst,
        COALESCE(ROUND(SUM(sgst),2), 0) AS sgst,
        COALESCE(ROUND(SUM(igst),2),0) AS igst FROM
        (SELECT hsn, SUM(price_subtotal) AS price_subtotal,
        COALESCE(SUM((cgst * price_subtotal) / 100), 0) AS cgst_val,
        COALESCE(SUM((sgst * price_subtotal) / 100),0) AS sgst_val,
        COALESCE(SUM((igst * price_subtotal) / 100), 0) AS igst_val,
        cgst,sgst,igst FROM
        (SELECT l10n_in_hsn_code AS hsn, aml.price_subtotal,
        CASE WHEN at.amount_type != 'group' THEN 0 ELSE
        (SELECT atc.amount FROM account_tax_filiation_rel atf
        JOIN account_tax atc ON (atc.id = atf.child_tax)
        JOIN account_tax_group satg ON (satg.id = atc.tax_group_id)
        AND at.id = atf.parent_tax AND satg.name = 'CGST') END AS cgst,
        CASE WHEN at.amount_type != 'group' THEN 0 ELSE
        (SELECT atc.amount FROM account_tax_filiation_rel atf
        JOIN account_tax atc ON (atc.id = atf.child_tax)
        JOIN account_tax_group satg ON (satg.id = atc.tax_group_id)
        AND at.id = atf.parent_tax AND satg.name = 'SGST') END AS sgst,
        CASE WHEN at.amount_type != 'group' THEN
        (SELECT atco.amount FROM account_tax atco
        JOIN account_tax_group satgo ON (satgo.id = atco.tax_group_id)
        WHERE atco.id = at.id AND satgo.name = 'IGST') ELSE 0 END AS igst
        FROM account_move_line aml
        JOIN product_product pp ON (pp.id = aml.product_id)
        JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
        JOIN account_move_line_account_tax_rel amr ON (amr.account_move_line_id = aml.id)
        JOIN account_tax at ON (at.id = amr.account_tax_id)
        JOIN account_tax_group atg ON (atg.id = at.tax_group_id)
        WHERE move_id = %s)temp
        GROUP BY hsn, price_subtotal, cgst, sgst, igst)temp1
        GROUP BY hsn, price_subtotal ''', (obj.id,))
        line_data = [i for i in self.env.cr.dictfetchall()]
        print("---", line_data, "--line_data--")
        if line_data:
            return line_data
        else:
            return [{'price_total': 0.00, 'description': ''}]

    def get_tds_des(self, obj):
        self.env.cr.execute('''
        SELECT COALESCE(SUM((at.amount * aml.price_subtotal) / 100), 0) AS total
        FROM account_move_line aml
        JOIN product_product pp ON (pp.id = aml.product_id)
        JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
        JOIN account_move_line_account_tax_rel amr ON (amr.account_move_line_id = aml.id)
        JOIN account_tax at ON (at.id = amr.account_tax_id)
        JOIN account_tax_group atg ON (atg.id = at.tax_group_id)
        WHERE move_id = %s AND atg.name = 'TDS' ''', (obj.id,))
        line_data = [i for i in self.env.cr.fetchall()]
        if line_data:
            return line_data[0][0]
        else:
            return 0.0

    def get_tax_tot_des(self, obj):
        self.env.cr.execute('''
        SELECT SUM(price_subtotal) AS price_subtotal, SUM(cgst_val) AS cgst_val, SUM(sgst_val) AS sgst_val, SUM(igst_val) AS igst_val FROM
        (SELECT hsn, sum(price_subtotal) as price_subtotal, SUM(cgst_val) AS cgst_val, SUM(sgst_val) AS sgst_val, SUM(igst_val) AS igst_val,
        COALESCE(ROUND(SUM(cgst),2), '0') AS cgst,
        COALESCE(ROUND(SUM(sgst),2), 0) AS sgst,
        COALESCE(ROUND(SUM(igst),2),0) AS igst FROM
        (SELECT hsn, SUM(price_subtotal) AS price_subtotal,
        COALESCE(SUM((cgst * price_subtotal) / 100), 0) AS cgst_val,
        COALESCE(SUM((sgst * price_subtotal) / 100),0) AS sgst_val,
        COALESCE(SUM((igst * price_subtotal) / 100), 0) AS igst_val,
        cgst,sgst,igst FROM
        (SELECT l10n_in_hsn_code AS hsn, aml.price_subtotal,
        CASE WHEN at.amount_type != 'group' THEN 0 ELSE
        (SELECT atc.amount FROM account_tax_filiation_rel atf
        JOIN account_tax atc ON (atc.id = atf.child_tax)
        JOIN account_tax_group satg ON (satg.id = atc.tax_group_id)
        AND at.id = atf.parent_tax AND satg.name = 'CGST') END AS cgst,
        CASE WHEN at.amount_type != 'group' THEN 0 ELSE
        (SELECT atc.amount FROM account_tax_filiation_rel atf
        JOIN account_tax atc ON (atc.id = atf.child_tax)
        JOIN account_tax_group satg ON (satg.id = atc.tax_group_id)
        AND at.id = atf.parent_tax AND satg.name = 'SGST') END AS sgst,
        CASE WHEN at.amount_type != 'group' THEN
        (SELECT atco.amount FROM account_tax atco
        JOIN account_tax_group satgo ON (satgo.id = atco.tax_group_id)
        WHERE atco.id = at.id AND satgo.name = 'IGST') ELSE 0 END AS igst
        FROM account_move_line aml
        JOIN product_product pp ON (pp.id = aml.product_id)
        JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
        JOIN account_move_line_account_tax_rel amr ON (amr.account_move_line_id = aml.id)
        JOIN account_tax at ON (at.id = amr.account_tax_id)
        JOIN account_tax_group atg ON (atg.id = at.tax_group_id)
        WHERE move_id = %s)temp
        GROUP BY hsn, price_subtotal, cgst, sgst, igst)temp1
        GROUP BY hsn, price_subtotal)temp2
        ''', (obj.id,))
        line_data = [i for i in self.env.cr.dictfetchall()]
        print("---", line_data, "--line_data--")
        if line_data:
            return line_data
        else:
            return [{'price_total': 0.00, 'description': ''}]

    def get_bank(self, obj):
        final = []
        data = {}
        for i in obj.company_id.partner_id.bank_ids:
            data['bank_holder'] = i.acc_holder_name
            data['bank_number'] = i.acc_number
            data['bank_name'] = i.bank_id.name
            data['bank_ifsc'] = i.bank_id.bic
        final.append(data)
        return final

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        print("---dsdfghsdfghbsdfg ----")
        self.invoice_cash_rounding_id = self.env['account.cash.rounding'].search([], limit=1).id

    def get_tax_ids_igst(self, obj):
        tax_ids_igst = []
        for i in obj.invoice_line_ids.tax_ids:
            if i.tax_group_id.name == 'IGST':
                tax_ids_igst.append(i.display_name)
            else:
                pass
        return tax_ids_igst

    def get_tax_ids_gst(self, obj):
        tax_ids_gst = []
        for i in obj.invoice_line_ids.tax_ids:
            if i.tax_group_id.name == 'GST':
                tax_ids_gst.append(i.display_name)
            else:
                pass
        return tax_ids_gst


class GstReport(models.AbstractModel):
    _name = 'report.mm_onscreen_report.gst_move_template_report'
    _description = 'GST Invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        inv = self.env['account.move'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': inv,
            'data': data,
        }

