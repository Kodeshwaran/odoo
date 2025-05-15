from odoo import api, fields, models, _


class ReportDueInvoice(models.AbstractModel):
    _name = "report.bell_account.report_due_invoices"

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        print('\n---',docs,'--docs--\n')
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': data,
            'docs': docs,
        }

    # @api.model
    # def get_report_values(self, docids, data=None):
    #     return {
    #         'doc_ids': data['ids'],
    #         'doc_model': data['model'],
    #         'date_start': date_start,
    #         'date_end': date_end,
    #         'docs': docs,
    #     }

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['account.payment'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': report_obj,
            'data': data,
            'amount_total_words': self.amount_total_words,
        }
        return self.env['ir.qweb'].render('bell_account.report_due_vendor_invoices', docargs)


class ReportDueVendorInvoice(models.AbstractModel):
    _name = 'report.bell_account.report_due_vendor_invoices'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        return {
            'data': data.get('form')
            }


class VendorListWizard(models.TransientModel):
    _name = 'vendor.list.wizard'
    _description = "Attendance Report Wizard"

    def print_report(self):
        domain = []
        datas = self.env['account.move'].search([('id', 'in', self._context.get('active_ids'))])
        # company = self.env['res.company'].search([('id', '=', self.env.user.company_id)])
        res = {
            'invoices': datas.ids,
            'company_id': self.env.user.company_id.id,
            'domain':  [('move_type', '=', 'in_invoice')]
        }
        data = {
            'form': res,
        }
        return self.env.ref('bell_account.report_due_invoices').report_action([], data=data)
