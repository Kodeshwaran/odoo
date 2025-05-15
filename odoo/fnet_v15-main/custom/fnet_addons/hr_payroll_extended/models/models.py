# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from calendar import monthrange
# from odoo.addons.base.ir.ir_mail_server import MailDeliveryException


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.depends('contract_id', 'employee_id', 'date_from', 'date_to')
    def _get_tot_work_days(self):
        for rec in self:
            from_date = fields.Date.from_string(rec.date_from)
            days = monthrange(from_date.year, from_date.month)[1]
            rec.tot_month_days = days

    @api.onchange('contract_id', 'employee_id', 'date_from', 'date_to')
    def onchange_start_date(self):
        lop_days = 0
        from_date = fields.Date.from_string(self.date_from)
        to_date = fields.Date.from_string(self.date_to)
        start = from_date.replace(day=1)
        end = from_date.replace(day=monthrange(from_date.year, from_date.month)[1])
        if from_date > start:
            lop_days += (from_date-start).days
        if to_date < end:
            lop_days += (end - to_date).days
        self.lop_days = lop_days

    lop_days=fields.Float('LOP Days')
    tot_month_days = fields.Float('Total days', compute='_get_tot_work_days', store=True)



class HrPayslipEmployees(models.TransientModel):
    _name = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees')

    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        rec_from_date = run_data.get('date_start')
        rec_to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            from_date = rec_from_date
            to_date = rec_to_date
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            print("\n---", employee, "--employee--\n")
            print("\n---", employee.contract_id, "--employee.contract_id--\n")
            print("\n---", employee.contract_id.date_start, "--employee.contract_id.date_start--\n")
            if not employee.contract_id:
                raise UserError(_("No Contracts are current active for %s" % employee.name))
            if employee.contract_id.date_start > from_date:
                from_date = employee.contract_id.date_start
            if employee.contract_id.date_end and employee.contract_id.date_end < to_date:
                to_date = employee.contract_id.date_end
            if to_date < from_date:
                raise UserError(
                    _("Payslip can not generate for employee %s. Kindly check Contract Date's." % (employee.name)))
            start_month = fields.Date.from_string(from_date)
            end_month = fields.Date.from_string(to_date)
            start = start_month.replace(day=1)
            end = start_month.replace(day=monthrange(start_month.year, start_month.month)[1])
            lop_days = 0
            if start_month > start:
                lop_days += (start_month - start).days
            if end_month < end:
                lop_days += (end - end_month).days

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'lop_days': lop_days,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
            }
            payslips += self.env['hr.payslip'].create(res)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payslip_mail = fields.Char(string="Payslip Email (From)", related='company_id.payslip_mail', readonly=False)

class ResCompany(models.Model):
    _inherit = 'res.company'

    payslip_mail = fields.Char(string="Payslip Email (From)")
