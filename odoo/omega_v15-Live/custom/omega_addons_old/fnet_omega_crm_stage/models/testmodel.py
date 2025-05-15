from datetime import datetime

from odoo import api, fields, models, tools
from odoo.exceptions import UserError, AccessError
from odoo.tools.translate import _


class MailTracking(models.Model):
    _inherit = 'mail.tracking.value'

    # @api.model
    # def create_tracking_values(self, initial_value, new_value, col_name, col_info):
    #     tracked = True
    #     values = {'field': col_name, 'field_desc': col_info['string'], 'field_type': col_info['type']}
    #     print("\n---", initial_value, "--initial_value--\n")
    #     print("\n---", new_value, "--new_value--\n")
    #     print("\n---", col_name, "--col_name--\n")
    #     print("\n---", col_info, "--col_info--\n")
    #     print("\n---", values, "--values--\n")
    #     if col_info['type'] in ['integer', 'float', 'char', 'text', 'datetime', 'monetary']:
    #         values.update({
    #             'old_value_%s' % col_info['type']: initial_value,
    #             'new_value_%s' % col_info['type']: new_value
    #         })
    #     elif col_info['type'] == 'many2one' and col_name == 'stage_ids1':
    #         if ((initial_value and initial_value.id or 0)) == 5:
    #             raise UserError(_('You Cannot Move Opportunity Which In Approved Stage!!!'))
    #
    #         elif ((initial_value and initial_value.id or 0) == 4 and (new_value and new_value.id or 0) >= 5):
    #             values.update({
    #                 'old_value_integer': initial_value and initial_value.id or 0,
    #                 'new_value_integer': new_value and new_value.id or 0,
    #                 'old_value_char': initial_value and initial_value.name_get()[0][1] or '',
    #                 'new_value_char': new_value and new_value.name_get()[0][1] or ''
    #             })
    #         elif ((initial_value and initial_value.id or 0) > (new_value and new_value.id or 0)):
    #             flag = self.env['res.users'].has_group('base.group_team_managers')
    #             if flag == False:
    #                 raise UserError(_('Sale Team Manager Only Can Move Stage In Backward !!!'))
    #             else:
    #                 values.update({
    #                     'old_value_integer': initial_value and initial_value.id or 0,
    #                     'new_value_integer': new_value and new_value.id or 0,
    #                     'old_value_char': initial_value and initial_value.name_get()[0][1] or '',
    #                     'new_value_char': new_value and new_value.name_get()[0][1] or ''
    #                 })
    #
    #         elif ((initial_value and initial_value.id or 0) < 4 and (new_value and new_value.id or 0) != 5):
    #             if (((initial_value and initial_value.id or 0) + 1) == (new_value and new_value.id or 0)):
    #                 values.update({
    #                     'old_value_integer': initial_value and initial_value.id or 0,
    #                     'new_value_integer': new_value and new_value.id or 0,
    #                     'old_value_char': initial_value and initial_value.name_get()[0][1] or '',
    #                     'new_value_char': new_value and new_value.name_get()[0][1] or ''
    #                 })
    #             elif (((initial_value and initial_value.id or 0) + 1) != (new_value and new_value.id or 0)):
    #                 if ((initial_value and initial_value.id or 0) < (new_value and new_value.id or 0)):
    #                     if ((initial_value and initial_value.id or 0) == 4 and (new_value and new_value.id or 0) >= 5):
    #                         values.update({
    #                             'old_value_integer': initial_value and initial_value.id or 0,
    #                             'new_value_integer': new_value and new_value.id or 0,
    #                             'old_value_char': initial_value and initial_value.name_get()[0][1] or '',
    #                             'new_value_char': new_value and new_value.name_get()[0][1] or ''
    #                         })
    #
    #                     elif ((initial_value and initial_value.id or 0) == 1 and (
    #                             new_value and new_value.id or 0) == 2):
    #                         values.update({
    #                             'old_value_integer': initial_value and initial_value.id or 0,
    #                             'new_value_integer': new_value and new_value.id or 0,
    #                             'old_value_char': initial_value and initial_value.name_get()[0][1] or '',
    #                             'new_value_char': new_value and new_value.name_get()[0][1] or ''
    #                         })
    #
    #                     elif ((initial_value and initial_value.id or 0) == 2 and (
    #                             new_value and new_value.id or 0) == 3):
    #                         values.update({
    #                             'old_value_integer': initial_value and initial_value.id or 0,
    #                             'new_value_integer': new_value and new_value.id or 0,
    #                             'old_value_char': initial_value and initial_value.name_get()[0][1] or '',
    #                             'new_value_char': new_value and new_value.name_get()[0][1] or ''
    #                         })
    #
    #                     elif ((initial_value and initial_value.id or 0) == 3 and (
    #                             new_value and new_value.id or 0) == 4):
    #                         values.update({
    #                             'old_value_integer': initial_value and initial_value.id or 0,
    #                             'new_value_integer': new_value and new_value.id or 0,
    #                             'old_value_char': initial_value and initial_value.name_get()[0][1] or '',
    #                             'new_value_char': new_value and new_value.name_get()[0][1] or ''
    #                         })
    #                     else:
    #                         raise UserError(_('You Cannot Directly Move To This Stage!!!'))
    #                     if ((initial_value and initial_value.id or 0)) == 5:
    #                         raise UserError(_('You Cannot Move Opportunity Which In Approved Stage!!!'))
    #                     else:
    #                         pass
    #     else:
    #         tracked = False
    #     if tracked:
    #         return values
    #     return {}

    @api.multi
    def get_old_display_value(self):
        result = []
        for record in self:
            if record.field_type in ['integer', 'float', 'char', 'text', 'datetime', 'monetary']:
                result.append(getattr(record, 'old_value_%s' % record.field_type))
            elif record.field_type == 'date':
                if record.old_value_datetime:
                    old_date = datetime.strptime(record.old_value_datetime, tools.DEFAULT_SERVER_DATETIME_FORMAT).date()
                    result.append(old_date.strftime(tools.DEFAULT_SERVER_DATE_FORMAT))
                else:
                    result.append(record.old_value_datetime)
            elif record.field_type == 'boolean':
                result.append(bool(record.old_value_integer))
            elif record.field_type in ['many2one', 'selection']:
                result.append(record.old_value_char)
            else:
                result.append(record.old_value_char)
        return result

    @api.multi
    def get_new_display_value(self):
        result = []
        for record in self:
            if record.field_type in ['integer', 'float', 'char', 'text', 'datetime', 'monetary']:
                result.append(getattr(record, 'new_value_%s' % record.field_type))
            elif record.field_type == 'date':
                if record.new_value_datetime:
                    new_date = datetime.strptime(record.new_value_datetime, tools.DEFAULT_SERVER_DATETIME_FORMAT).date()
                    result.append(new_date.strftime(tools.DEFAULT_SERVER_DATE_FORMAT))
                else:
                    result.append(record.new_value_datetime)
            elif record.field_type == 'boolean':
                result.append(bool(record.new_value_integer))
            elif record.field_type in ['many2one', 'selection']:
                result.append(record.new_value_char)
            else:
                result.append(record.new_value_char)
        return result
