# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import json
import xlsxwriter
import base64
import io


class L10nInReportAccount(models.AbstractModel):
    _inherit = 'l10n.in.report.account'

    def _get_reports_buttons(self, options):
        buttons = super(L10nInReportAccount, self)._get_reports_buttons(options)
        buttons.append({'name': _('EXCEL'), 'action': 'print_excel'})
        return buttons

    def _get_columns_name_all(self, options):
        columns = ['Section', 'Number of Entries', 'Total CGST', 'Total SGST', 'Total IGST', 'Total CESS']
        return [{'name': _(col), 'class': 'number o_account_reports_level0'} if 'Total' in col else {'name': _(col),
                                                                                                     'class': "o_account_reports_level0"}
                for col in columns]

    def _get_lines_main(self, options, gst_return_type, gst_section):
        lines = []
        filter_domain = [
            ('date', '>=', options['date'].get('date_from')),
            ('date', '<=', options['date'].get('date_to')),
            ('company_id', 'in', self.env.companies.ids)
        ]
        filter_domain += self._get_options_journals_domain(options)
        context = self.env.context
        if context.get('partner_ids'):
            filter_domain += [('partner_id', 'in', context['partner_ids'].ids)]
        if context.get('partner_categories'):
            filter_domain += [('partner_id.category_id', 'in', context['partner_categories'].ids)]

        model_domain = self.get_gst_section_model_domain(gst_return_type, gst_section)
        domain = filter_domain + model_domain.get('domain')
        fields_values = self.env[model_domain.get('model')].search(domain).union().read()
        lines += self.set_gst_section_lines(gst_return_type, gst_section, fields_values)
        return lines

    def _get_lines_all(self, options, line_id=None):
        lines = []
        gst_return_type = options.get('gst_return_type')
        gst_section = options.get('gst_section')
        filter_domain = [
            ('date', '>=', options['date'].get('date_from')),
            ('date', '<=', options['date'].get('date_to')),
            ('company_id', 'in', self.env.companies.ids)]
        context = self.env.context
        filter_domain += self._get_options_journals_domain(options)
        for gst_section, gst_section_name in self.get_gst_section(gst_return_type).items():
            total_cgst = total_sgst = total_igst = total_cess = 0
            move_count_dict = {}
            model_domain = self.get_gst_section_model_domain(gst_return_type, gst_section)
            domain = filter_domain + model_domain.get('domain')
            for read_data in self.env[model_domain.get('model')].search(domain).union().read(
                    model_domain.get('sum_fields')):
                total_cess += read_data.get('cess_amount', 0)
                total_igst += read_data.get('igst_amount', 0)
                total_cgst += read_data.get('cgst_amount', 0)
                total_sgst += read_data.get('sgst_amount', 0)
                move_count_dict.setdefault(read_data.get('account_move_id'))
            columns = [
                {'value': len(move_count_dict)},
                {'value': self.format_value(total_cgst), 'class': 'number'},
                {'value': self.format_value(total_sgst), 'class': 'number'},
                {'value': self.format_value(total_igst), 'class': 'number'},
                {'value': self.format_value(total_cess), 'class': 'number'}]
            lines.append({
                'id': '%s_%s' % (gst_return_type, gst_section),
                'name': gst_section_name,
                'level': 2,
                'colspan': 0,
                'columns': [{
                    'name': v.get('value'),
                    'class': v.get('class', '')} for v in columns],
                'action_id': self.env.ref('l10n_in_reports.action_l10n_in_report_account').id,
                'action': 'view_sub_type'
            })
        return lines

    def print_excel(self, options):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        header_format = workbook.add_format({'bold': True, 'valign': 'vcenter', 'bg_color': '#D3D3D3', 'border': 1})
        cell_format = workbook.add_format({'border': 1})
        number_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})

        def set_column_widths(sheet, widths):
            for i, width in enumerate(widths):
                sheet.set_column(i, i, width)

        def write_headers(sheet, headers):
            for col, header in enumerate(headers):
                sheet.write(0, col, header['name'], header_format)

        def write_lines(sheet, lines):
            for row, line in enumerate(lines, 1):
                sheet.write(row, 0, line['name'], cell_format)
                for col, column in enumerate(line['columns']):
                    fmt = number_format if column.get('class') == 'number' else cell_format
                    sheet.write(row, col + 1, column['name'], fmt)

        sheets_info = [
            ("Summary", self._get_columns_name_all(options), self._get_lines_all(options),
             [65, 20, 20, 20, 20, 20]),
            ("B2B", self.get_gst_section_fields('gstr1', 'b2b'),
             self._get_lines_main(options, 'gstr1', 'b2b'), [35, 20, 35, 15, 15, 15, 15, 15, 15, 15]),
            ("B2C", self.get_gst_section_fields('gstr1', 'b2cl'),
             self._get_lines_main(options, 'gstr1', 'b2cl'), [35, 20, 20, 20, 20, 20, 20, 20, 20, 20]),
            ("Credit Note", self.get_gst_section_fields('gstr1', 'cdnr'),
             self._get_lines_main(options, 'gstr1', 'cdnr'), [40, 40, 20, 20, 20, 20, 20, 20, 20]),
            ("Export", self.get_gst_section_fields('gstr1', 'exp'),
             self._get_lines_main(options, 'gstr1', 'exp'), [40, 40, 20, 20, 20])
        ]

        for sheet_name, headers, lines, widths in sheets_info:
            sheet = workbook.add_worksheet(sheet_name)
            set_column_widths(sheet, widths)
            write_headers(sheet, headers)
            write_lines(sheet, lines)

        workbook.close()
        output.seek(0)

        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': 'GSTR-1 Sales Return.xlsx',
            'res_model': 'ir.ui.view',
            'res_id': False,
            'type': 'binary',
            'public': True,
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        download_url = f"/web/content/{attachment_id.id}?download=True"
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        return {
            "type": "ir.actions.act_url",
            "url": f"{base_url}{download_url}",
            "target": "new",
        }

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        gst_return_type = options.get('gst_return_type')
        gst_section = options.get('gst_section')
        filter_domain = [
            ('date', '>=', options['date'].get('date_from')),
            ('date', '<=', options['date'].get('date_to')),
            ('company_id', 'in', self.env.companies.ids)]
        context = self.env.context
        if context.get('partner_ids'):
            filter_domain += [
                ('partner_id', 'in', context['partner_ids'].ids)]
        if context.get('partner_categories'):
            filter_domain += [
                ('partner_id.category_id', 'in', context['partner_categories'].ids)]
        filter_domain += self._get_options_journals_domain(options)
        if gst_section:
            model_domain = self.get_gst_section_model_domain(gst_return_type, gst_section)
            fields_values = self.env[model_domain.get('model')].search(
                filter_domain + model_domain.get('domain')).union().read()
            lines += self.set_gst_section_lines(
                gst_return_type,
                gst_section,
                fields_values)
        else:
            for gst_section, gst_section_name in self.get_gst_section(gst_return_type).items():
                total_amount = total_cgst = total_sgst = total_igst = total_cess = 0
                move_count_dict = {}
                model_domain = self.get_gst_section_model_domain(gst_return_type, gst_section)
                domain = filter_domain + model_domain.get('domain')
                for read_data in self.env[model_domain.get('model')].search(domain).union().read(
                        model_domain.get('sum_fields')):
                    # total_cess += read_data.get('cess_amount', 0)
                    total_amount += read_data.get('total', 0)
                    total_igst += read_data.get('igst_amount', 0)
                    total_cgst += read_data.get('cgst_amount', 0)
                    total_sgst += read_data.get('sgst_amount', 0)
                    move_count_dict.setdefault(read_data.get('account_move_id'))
                columns = [
                    {'value': len(move_count_dict)},
                    {'value': self.format_value(total_amount), 'class': 'number'},
                    {'value': self.format_value(total_cgst), 'class': 'number'},
                    {'value': self.format_value(total_sgst), 'class': 'number'},
                    {'value': self.format_value(total_igst), 'class': 'number'},
                    ]
                lines.append({
                    'id': '%s_%s' % (gst_return_type, gst_section),
                    'name': gst_section_name,
                    'level': 2,
                    'colspan': 0,
                    'columns': [{
                        'name': v.get('value'),
                        'class': v.get('class', '')} for v in columns],
                    'action_id': self.env.ref('l10n_in_reports.action_l10n_in_report_account').id,
                    'action': 'view_sub_type'
                })
        return lines

    def _get_columns_name(self, options):
        res = super(L10nInReportAccount, self)._get_columns_name(options)
        gst_section = options.get('gst_section')
        if not gst_section:
            res.insert(2, {'name': _('Total Gross Amount'), 'class': 'number o_account_reports_level0'})
            for sec in res:
                if sec['name'] == _('Total CESS'):
                    res.remove(sec)
        return res


    def get_gst_section_fields(self, gst_return_type, gst_section):
        res = super(L10nInReportAccount, self).get_gst_section_fields(gst_return_type, gst_section)
        for section in res:
            if section['name'] == 'cess_amount':
                res.remove(section)
        if gst_section in ['b2b', 'b2cl']:
            res.append({'name': 'sgst_amount', 'label': 'SGST', 'class': 'number'})
            res.append({'name': 'cgst_amount', 'label': 'CGST', 'class': 'number'})
            res.append({'name': 'igst_amount', 'label': 'IGST', 'class': 'number'})
        elif gst_section in ['cdnr', 'cdnur']:
            res = [
                {"name": "account_move_id", "label": "Invoice Number"},
                {'name': 'partner_id', 'label': 'Partner Name'},
                {'name': 'partner_vat', 'label': 'GST'},
                {"name": "gst_format_date", "label": "Invoice date"},
                {"name": "price_total", "label": "Untaxed Amount"},
                {"name": "total", "label": "Gross Amount"},
                {"name": "sgst_amount", "label": "SGST"},
                {"name": "cgst_amount", "label": "CGST"},
                {"name": "igst_amount", "label": "IGST"},
            ]
        elif gst_section == 'exp':
            res = [
                    {"name": "account_move_id", "label": "Invoice Number"},
                    {'name': 'partner_id', 'label': 'Partner Name'},
                    {"name": "gst_format_date", "label": "Invoice date"},
                    # {"name": "export_type", "label": "Export Type"},
                    # {"name": "shipping_port_code_id", "label": "Port Code"},
                    # {"name": "shipping_bill_number", "label": "Shipping Bill Number"},
                    # {"name": "gst_format_shipping_bill_date", "label": "Shipping Bill Date"},
                    # {"name": "tax_rate", "label": "Rate"},
                    {"name": "price_total", "label": "Untaxed Amount"},
                    {"name": "total", "label": "Gross Amount"},
                    ]
            # res.insert(1, {'name': 'partner_id', 'label': 'Partner Name'})
        return res