# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_task_alert = fields.Boolean(string="Enable Task Remainder", related="company_id.enable_task_alert", readonly=False)
    task_deadline_alert_type = fields.Selection([
        ('single', "Remainder on task's expected end date"),
        ('multi', 'Remainder before few days'),
        ('everyday', "Everyday till task's expected end date"),
        ('everyday_after', "Remainder on and after task's expected end date")
    ], string='Email Remainder Type', related='company_id.task_deadline_alert_type', readonly=False,
        help="""
                   Email Remainder on task's expected end date: You will get notification only on expected end date.
                   Email Remainder before few days: You will get notification in few days.On expected end date and number of days before end date.
                   Everyday till task's expected end date: You will get notification from start till the expected end date of the task.
                   Email Remainder on and after task's expected end date: You will get notification on the expected end date and continues upto Days.
                   If you did't select any then you will get notification on the expected end date.""")
    task_deadline_alert_day = fields.Integer(string="Days", help="How many number of days before to get the notification email",
                                 readonly=False, related="company_id.task_deadline_alert_day")
    enable_timesheet_alert = fields.Boolean(string="Enable Timesheet Remainder", readonly=False, related="company_id.enable_timesheet_alert")
    timesheet_alert_day = fields.Integer('Sent alert if not register more than', help="Remainder for not entering timesheet more than configured days", readonly=False, related="company_id.timesheet_alert_day")
    project_email = fields.Char('Project Email', readonly=False, related='company_id.project_email', store=True)
    purchase_email = fields.Char('Purchase Email', readonly=False, related='company_id.purchase_email', store=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    project_email = fields.Char('Project Email')
    purchase_email = fields.Char('Purchase Email')
    enable_task_alert = fields.Boolean(string="Enable Task Remainder", readonly=False)
    task_deadline_alert_type = fields.Selection([
        ('single', "Remainder on task's Deadline"),
        ('multi', 'Remainder before few days'),
        ('everyday', "Everyday till task's Deadline"),
        ('everyday_after', "Remainder on and after task's Deadline")
    ], string='Email Remainder Type', readonly=False,
        help="""
                   Email Remainder on task's expected end date: You will get notification only on expected end date.
                   Email Remainder before few days: You will get notification in few days.On expected end date and number of days before end date.
                   Everyday till task's expected end date: You will get notification from start till the expected end date of the task.
                   Email Remainder on and after task's expected end date: You will get notification on the expected end date and continues upto Days.
                   If you did't select any then you will get notification on the expected end date.""")
    task_deadline_alert_day = fields.Integer(string="Days", help="How many number of days before to get the notification email")

    enable_timesheet_alert = fields.Boolean(string="Enable Timesheet Remainder", readonly=False)
    timesheet_alert_day = fields.Integer('Configuration Days', help="Remainder for not entering timesheet more than configured days", readonly=False)



