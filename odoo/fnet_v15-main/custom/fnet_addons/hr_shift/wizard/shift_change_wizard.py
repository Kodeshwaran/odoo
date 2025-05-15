from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ShiftChangeRequestWizard(models.TransientModel):
    _name = 'shift.change.request.wizard'
    _description = 'HR Shift Change Request Wizard'

    desired_shift = fields.Many2one('hr.shift', 'Desired Shift', domain="[('name', '!=', 'WeekOff'), ('id', '!=', assigned_emp_shift)]", required=True)
    assigned_emp = fields.Many2one('hr.employee.shift', 'Assigned Employee')
    assigned_emp_level = fields.Selection([('l1', 'L1'), ('l2', 'L2'), ('l3', 'L3'), ('l4', 'L4')], related='assigned_emp.employee_level', store=True)
    assigned_emp_shift_date = fields.Date(related="assigned_emp.date")
    assigned_emp_id = fields.Many2one(related="assigned_emp.employee_id")
    assigned_emp_shift = fields.Many2one(related="assigned_emp.shift_id")
    desired_emp_swap = fields.Many2one('hr.employee.shift', "Shift to Swap")
    desired_emp_level = fields.Selection([('l1', 'L1'), ('l2', 'L2'), ('l3', 'L3'), ('l4', 'L4')], related='desired_emp_swap.employee_level')
    desired_emp_shift_date = fields.Date(related="desired_emp_swap.date")
    desired_emp_id = fields.Many2one(related="desired_emp_swap.employee_id")
    desired_emp_shift = fields.Many2one(related="desired_emp_swap.shift_id")

    @api.onchange('assigned_emp', 'desired_shift')
    def onchange_desired_shift(self):
        shifts = []
        if self.desired_shift:
            shifts += self.env['hr.employee.shift'].search([
                ('shift_id', '=', self.desired_shift.id),
                ('date', '=', self.assigned_emp_shift_date),
                ('employee_id', '!=', self.assigned_emp_id.id)]).ids
        return {'domain': {'desired_emp_swap': [('id', 'in', shifts)]}}


    def action_confirm_wizard(self):
        today = fields.Date.today()
        if self.desired_emp_shift_date <= today:
            raise UserError("You cannot request shift change for shifts created in past.")
        shift_change_req = self.env['shift.change.request'].create({
            'state': 'send',
            'employee_assigned_id': str(self.assigned_emp.employee_id.name),
            'shift_assigned_id': str(self.assigned_emp.shift_id.name),
            'assigned_date': str(self.assigned_emp.date.strftime('%d-%m-%Y')),
            'assigned_start_time': self.assigned_emp.start_time,
            'assigned_end_time': self.assigned_emp.end_time,
            'employee_requested_id': str(self.desired_emp_id.name),
            'shift_requested_id': str(self.desired_emp_shift.name),
            'requested_date': str(self.desired_emp_swap.date.strftime('%d-%m-%Y')),
            'requested_start_time': self.desired_emp_swap.start_time,
            'requested_end_time': self.desired_emp_swap.end_time,
            'assigned_emp_shift': self.assigned_emp.id,
            'requested_emp_shift': self.desired_emp_swap.id,
            'assigned_shift_id': self.assigned_emp_shift.id,
            'replaced_shift_id': self.desired_emp_shift.id,
            'employee_assigned_name': self.assigned_emp_id.id,
            'employee_requested_name': self.desired_emp_id.id,
        })
        return shift_change_req






