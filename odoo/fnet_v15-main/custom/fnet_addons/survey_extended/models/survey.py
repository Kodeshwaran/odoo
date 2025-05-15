# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, http, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import random
from datetime import date
import datetime
from odoo.tools import html2plaintext
from bs4 import BeautifulSoup


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    is_name = fields.Boolean('Is Name')
    is_company = fields.Boolean('Is Company')
    is_otp = fields.Boolean('Is OTP')
    is_important = fields.Boolean('Is Important')
    important_msg = fields.Html('Important Message')

    # def get_name(self):



class SurveyQuestionAnswer(models.Model):
    _inherit = 'survey.question.answer'

    findings = fields.Html(string='Findings')
    explanation = fields.Html(string='Explanation')
    recommendations = fields.Html(string='Recommendations')

class ContractConfiguration(models.Model):
    _inherit = 'survey.user_input'

    # survey_email = fields.Char(compute='_compute_survey', store=True)
    survey_email = fields.Char(string='Email')
    # user_name = fields.Char(compute="_compute_survey", store=True)
    user_name = fields.Char()
    otp_code = fields.Char(string="OTP Code")
    answer_otp = fields.Char(string="Answer otp")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def write(self, vals):
        res = super(ContractConfiguration, self).write(vals)
        for record in self:
            if vals.get('state') == 'done' and record.survey_email:
                record.session_end_result_mail()
        return res

    @api.onchange('state')
    def session_end_result_mail(self):
        print("--------", 111111111111111111, "----111111111111111111---\n")
        if self.state == 'done' and self.survey_email:
            print("--------", 111111111111111111, "----111111111111111111---\n")
            print("--------", self.company_id.name,"----self.company_id.name---\n")
            mail_template = self.env.ref('survey_extended.done_ref_survey_email')
            print("--------", mail_template, "----mail_template---\n")
            mail_template.sudo().send_mail(self.id, force_send=True)

    def generate_otp(self, length=4):
        self.otp_code = ''.join([str(random.randint(0, 9)) for _ in range(length)])
        # rec.write({'survey_email': line.value_char_box})
        return self.otp_code

    def send_otp_email(self):
        self.generate_otp()
        subject = "Your OTP for Verification"
        body = f"Dear User,\n\nYour OTP for verification is: {self.otp_code}\n\nThank you!"

        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': self.survey_email,
        }
        self.env['mail.mail'].create(mail_values).send()


    @api.depends('user_input_line_ids')
    def _compute_survey(self):
        for rec in self:
            rec.survey_email = ""
            rec.user_name = ""
            rec.answer_otp = ""
            for line in rec.user_input_line_ids:
                if line.question_id.is_name:
                    rec.write({'user_name': line.value_char_box})
            if rec.user_name and rec.survey_email and rec.state == "done" and rec.survey_id.confirmation_email:
                mail_template = self.sudo().env.ref('survey_extended.confirmation_survey_email')
                mail_template.sudo().send_mail(rec.id, force_send=True)

class Survey(models.Model):
    _inherit = 'survey.survey'
    _rec_name = 'rec_new'
    # print('\n------------', rec_name, '-------rec_name--------')

    survey_type = fields.Selection([('event', 'Event'), ('survey', 'Survey')], string='Type')
    venue_address = fields.Text()
    event_time = fields.Char()
    date_of_event = fields.Date()
    address_url = fields.Char()
    gentle_remainder = fields.Boolean()
    confirmation_email = fields.Boolean()
    start_button_name = fields.Char()
    image_logo = fields.Binary('Image', store=True, tracking=True,)
    file_name = fields.Char(string="File Name")
    first_score = fields.Html('First Score')
    second_score = fields.Html('Second Score')
    third_score = fields.Html('Third Score')
    rec_new = fields.Char("Rec Name", compute="_compute_rec_name", store=True)
    title = fields.Html("Title")

    @api.depends("title")
    def _compute_rec_name(self):
        for rec in self:
            if rec.title:
                soup = BeautifulSoup(rec.title, "html.parser")
                rec.rec_new = soup.get_text(separator=" ", strip=True)
            else:
                rec.rec_new = ""

    @api.model
    def create(self, vals):
        if "title" in vals:
            if vals["title"]:
                soup = BeautifulSoup(vals["title"], "html.parser")
                vals["rec_new"] = soup.get_text(separator=" ", strip=True)
            else:
                vals["rec_new"] = ""

        survey = super(Survey, self).create(vals)

        if vals.get("certification_give_badge"):
            survey.sudo()._create_certification_badge_trigger()

        return survey

    def write(self, vals):
        if "title" in vals:
            for rec in self:
                if vals["title"]:
                    soup = BeautifulSoup(vals["title"], "html.parser")
                    vals["rec_new"] = soup.get_text(separator=" ", strip=True)
                else:
                    vals["rec_new"] = ""

        result = super(Survey, self).write(vals)

        if "certification_give_badge" in vals:
            return self.sudo()._handle_certification_badges(vals)

        return result




    contact_details = fields.Html('Contact Details')
    # rec_ = fields.Char("Rec Name")
    # otp = generate_otp()



    def survey_gentle_remainder(self):
        first_event_date = date.today() + timedelta(days=1)
        survey_ids = self.env['survey.survey'].search([('date_of_event', '=', first_event_date)])
        second_first_event_date = date.today() + timedelta(days=2)
        survey_ids += self.env['survey.survey'].search([('date_of_event', '=',second_first_event_date)])
        for survey in survey_ids:
            if survey.gentle_remainder and survey.active:
                for rec in survey.user_input_ids:
                    if rec.state == 'done' and rec.survey_email:
                        mail_template = self.env.ref('survey_extended.gentle_remainder_survey_email')
                        mail_template.sudo().send_mail(rec.id, force_send=True)

    def session_close_email(self):
        for rec in self.user_input_ids:
            if rec.state == 'done' and rec.survey_email:
                mail_template = self.env.ref('survey_extended.thanks_survey_email')
                mail_template.sudo().send_mail(rec.id, force_send=True)

    def get_answer(self, access_token):
        answer = self.env['survey.user_input'].search([('access_token', '=', access_token)], limit=1)
        return answer


    # def is_important_survey(self):
    #     for rec in self.question_and_page_ids:
    #         if rec.question_and_page_ids == self.is_important:
