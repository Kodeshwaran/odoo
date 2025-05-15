from odoo import fields, models, _
from odoo.exceptions import ValidationError


class NoDueValidation(models.TransientModel):
    _name = 'no.due.validate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_approval = fields.Selection(selection=lambda self: self.compute_selection(), default=False)
    no_due_id = fields.Many2one('no.due')
    is_finance = fields.Boolean(related='no_due_id.is_finance')
    is_hr = fields.Boolean(related='no_due_id.is_hr')
    is_admin = fields.Boolean(related='no_due_id.is_admin')
    is_manager = fields.Boolean(related='no_due_id.is_manager')
    is_it = fields.Boolean(related='no_due_id.is_it')

    def compute_selection(self):
        selection = []
        no_due = self.env['no.due'].search([('id', '=', self.env.context.get('active_ids'))])
        if no_due:
            if no_due.is_finance:
                add_finance = ('finance', 'Finance')
                selection.insert(0, add_finance)
            if no_due.is_hr:
                add_hr = ('hr', 'HR')
                selection.insert(1, add_hr)
            if no_due.is_admin:
                add_admin = ('admin', 'Admin')
                selection.insert(2, add_admin)
            if no_due.is_manager:
                add_manager = ('manager', 'Manager')
                selection.insert(3, add_manager)
            if no_due.is_it:
                add_it = ('it', 'IT Department Head')
                selection.insert(4, add_it)
        return selection

    def validate_no_due(self):
        if not self.user_approval:
            raise ValidationError(_("Please identify the authority."))
        if self.user_approval == 'finance':
            if self.no_due_id.is_finance:
                if self.no_due_id.is_finance_approved:
                    raise ValidationError('Finance Approval Already Completed')
                if not self.no_due_id.salary_adv_taken or not self.no_due_id.travel_settlement or not self.no_due_id.loan_amount or not self.no_due_id.income_tax_details or not self.no_due_id.pt_deduct:
                    raise ValidationError(_('Please fill the details...'))
                self.no_due_id.write({'is_finance_approved': True})
                self.no_due_id.sudo().message_post(body='Finance Approval has been done by %s' % (self.env.user.name),
                                                   subject='Approval')
        elif self.user_approval == 'hr':
            if self.no_due_id.is_hr:
                if self.no_due_id.is_hr_approved:
                    raise ValidationError('HR Approval Already Completed')
                if not self.no_due_id.update_records or not self.no_due_id.remove_insurance or not self.no_due_id.biometric_removal or not self.no_due_id.sim_deactivation or not self.no_due_id.remove_number_whatsapp or not self.no_due_id.google_sheet or not self.no_due_id.closed_contract:
                    raise ValidationError(_('Please fill the details...'))
                self.no_due_id.write({'is_hr_approved': True})
                self.no_due_id.sudo().message_post(body='HR Approval has been done by %s' % (self.env.user.name),
                                                   subject='Approval')
        elif self.user_approval == 'admin':
            if self.no_due_id.is_admin:
                if self.no_due_id.is_admin_approved:
                    raise ValidationError('Admin Approval Already Completed')
                if not self.no_due_id.badge_and_card or not self.no_due_id.keys_handed_over or not self.no_due_id.mobile_and_sim or not self.no_due_id.insurance_card:
                    raise ValidationError(_('Please fill the details...'))
                self.no_due_id.write({'is_admin_approved': True})
                self.no_due_id.sudo().message_post(body='Admin Approval has been done by %s' % (self.env.user.name),
                                                   subject='Approval')
        elif self.user_approval == 'manager':
            if self.no_due_id.is_manager:
                if self.no_due_id.is_manager_approved:
                    raise ValidationError('Manager Approval Already Completed')
                if not self.no_due_id.kt_done or not self.no_due_id.related_data or not self.no_due_id.completed_tenure:
                    raise ValidationError(_('Please fill the details...'))
                self.no_due_id.write({'is_manager_approved': True})
                self.no_due_id.sudo().message_post(body='Manager Approval has been done by %s' % (self.env.user.name),
                                                   subject='Approval')
        elif self.user_approval == 'it':
            if self.no_due_id.is_it:
                if self.no_due_id.is_it_approved:
                    raise ValidationError('IT Department Head Approval Already Completed')
                if not self.no_due_id.ad_login_details or not self.no_due_id.erp_login_details or not self.no_due_id.email_disable or not self.no_due_id.materials_handed:
                    raise ValidationError(_('Please fill the details...'))
                self.no_due_id.write({'is_it_approved': True})
                self.no_due_id.sudo().message_post(
                    body='IT Department Head Approval has been done by %s' % (self.env.user.name), subject='Approval')
        if self.no_due_id.is_finance_approved and self.no_due_id.is_hr_approved and self.no_due_id.is_it_approved and self.no_due_id.is_admin_approved and self.no_due_id.is_manager_approved:
            self.no_due_id.write({'state': 'validated'})
            self.no_due_id.name.departure_date = self.no_due_id.date_of_resignation
            self.no_due_id.name.contract_id.date_end = self.no_due_id.date_of_resignation
            self.no_due_id.name.departure_reason_id = self.env.ref('hr.departure_resigned', False)
            self.no_due_id.name.active = False
