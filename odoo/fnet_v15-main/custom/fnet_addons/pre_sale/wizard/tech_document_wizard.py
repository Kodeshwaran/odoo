# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class TechDocumentWizard(models.TransientModel):
    _name = 'tech.document.wizard'
    _description = 'Tech Document'

    opportunity_id = fields.Many2one('crm.lead')
    version_name = fields.Char(string='Version Name')
    tech_file = fields.Many2many('ir.attachment', string='Technical Document')

    def update_document(self):
        if not self.version_name:
            raise UserError('Kindly enter the Version Name')
        elif not self.tech_file:
            raise UserError('Kindly attach the Technical Document')
        else:
            values = {
                'name': self.version_name,
                'date': fields.Datetime.now(),
                'document_attachment': [(6, 0, self.tech_file.ids)],
            }
            self.opportunity_id.write({'technical_file': [(6, 0, self.tech_file.ids)], 'attachment_tracking_ids': [(0, 0, values)]})
