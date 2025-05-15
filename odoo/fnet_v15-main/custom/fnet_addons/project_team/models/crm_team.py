# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class CrmTeamInherit(models.Model):
    _inherit = 'crm.team'

    type_team = fields.Selection([('sale', 'Sale'), ('project', 'Project')],
                                 "Type", default="sale")
    # type_project = fields.Selection([('project', 'Project'), ('odoo', 'Odoo')], "Project Type", required=True)
    team_members_ids = fields.Many2many('res.users', 'project_team_user_rel',
                                        'team_id', 'user_id', 'Project Members',
                                        help="""Project's members are users who
                                     can have an access to the tasks related
                                     to this project.""")
    project_visibility = fields.Selection([('lead', 'Only for Team Leader'), ('all', 'All Team Members')],
                                 "Project Visibility", default="all")

    @api.model
    def create(self, vals):
        res = super(CrmTeamInherit, self).create(vals)
        if 'team_members_ids' in vals:
            res._remove_user_from_other_teams()
        return res

    def write(self, vals):
        res = super(CrmTeamInherit, self).write(vals)
        if 'team_members_ids' in vals:
            self._remove_user_from_other_teams()
        return res

    def _remove_user_from_other_teams(self):
        for record in self:
            for user in record.team_members_ids:
                other_teams = self.search([('id', '!=', record.id), ('team_members_ids', 'in', user.id)])
                for team in other_teams:
                    team.team_members_ids = [(3, user.id)]