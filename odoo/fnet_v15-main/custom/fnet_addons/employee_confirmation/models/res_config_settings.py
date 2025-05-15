# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    probation_hr_mail = fields.Char('HR')
    birthday_wedding_wishes = fields.Boolean(string='Birthday And Wedding wishes')
    wishes_mail_cc = fields.Char(string="Wishes Mail(CC)")
    birthday_message = fields.Html(string="Birthday Message")
    wedding_message = fields.Html(string="Wedding Message")
    birthday_image = fields.Binary('Birthday Image')
    birthday_filename = fields.Char('Filename', size=64, readonly=True)
    wedding_image = fields.Binary('Wedding Image')
    wedding_filename = fields.Char('Filename', size=64, readonly=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    probation_hr_mail = fields.Char('HR', related='company_id.probation_hr_mail', readonly=False, store=True)
    birthday_wedding_wishes = fields.Boolean(string='Birthday And Wedding wishes', related='company_id.birthday_wedding_wishes', readonly=False, store=True)
    wishes_mail_cc = fields.Char(string="Wishes Mail(CC)", related='company_id.wishes_mail_cc', readonly=False, store=True)
    birthday_message = fields.Html(string="Birthday Message", related='company_id.birthday_message', readonly=False, store=True)
    wedding_message = fields.Html(string="Wedding Message", related='company_id.wedding_message', readonly=False, store=True)
    birthday_image = fields.Binary('Birthday Image', related='company_id.birthday_image', readonly=False, store=True)
    birthday_filename = fields.Char('Filename', size=64, readonly=True, related='company_id.birthday_filename', store=True)
    wedding_image = fields.Binary('Wedding Image', related='company_id.wedding_image', readonly=False, store=True)
    wedding_filename = fields.Char('Filename', size=64, readonly=True, related='company_id.wedding_filename', store=True)
