from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Refusal(models.TransientModel):
    _name = 'probation.review.refusal'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    probation_review_action = fields.Selection([('me', 'Meets Expectations-Successful Completion of Probationary Period'),
                                                ('dm', 'Does not meet Expectations'),
                                                ('ri', 'Requires Improvement')],
                                               related="probation_id.probation_review_action")
    refusal_reason = fields.Text()
    probation_id = fields.Many2one('probation.review')

    def generate_message_post(self):
        if self.probation_id:
            if self.probation_id.is_manager and self.probation_id.is_hod:
                self.probation_id.write({
                    'state': 'hod_approve',
                    'hod_comments': self.refusal_reason,
                })
                self.probation_id.sudo().message_post(body='%s' % self.refusal_reason, subject='Rejection Reason')
            elif self.probation_id.is_manager:
                self.probation_id.write({
                    'state': 'manager_approve',
                    'manager_comments': self.refusal_reason,
                })
                self.probation_id.sudo().message_post(body='%s' % self.refusal_reason, subject='Rejection Reason')
            elif self.probation_id.is_hod:
                self.probation_id.write({
                    'state': 'hod_approve',
                    'hod_comments': self.refusal_reason,
                })
                self.probation_id.sudo().message_post(body='%s' % self.refusal_reason,
                                                         subject='Rejection Reason')