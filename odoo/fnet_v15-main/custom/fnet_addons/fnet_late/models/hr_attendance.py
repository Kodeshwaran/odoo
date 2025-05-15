from odoo import models, fields, api, _
from datetime import datetime, timedelta, time
import xlsxwriter
import base64
import json
import urllib.parse  # Ensure URL encoding
from io import BytesIO
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta  # ✅ Add this line


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    late_count = fields.Integer(string="Late Count", compute="_compute_late_count")
    show_manager = fields.Boolean(default=False)

    def send_late_arrival_report(self):
        attachment = self.env['hr.late.approval'].generate_late_arrival_report()
        hr_email = 'vanakkamdamapla@gmail.com'

        mail_values = {
            'subject': "Weekly Late Arrivals Report",
            'email_from': self.env.user.company_id.email,
            'email_to': hr_email,
            'body_html': "<p>Dear HR,</p><p>Attached is the late arrivals report for this week.</p>",
            'attachment_ids': [(6, 0, [attachment.id])]
        }

        mail = self.env['mail.mail'].create(mail_values)
        mail.sudo().send()

    def _compute_late_count(self):
        for record in self:
            if record:
                today = fields.Date.today()
                previous_month = today.month - 1 if today.month > 1 else 12
                previous_year = today.year - 1 if today.month == 1 else today.year

                # Start date: 26th of previous month
                start_date = datetime(previous_year, previous_month, 26)

                # End date: 27th of current month
                end_date = datetime(today.year, today.month, 20)

                late_threshold = timedelta(hours=9, minutes=15)

                late_attendances = self.env['hr.attendance'].search_count([
                    ('employee_id', '=', record.id),
                    ('check_in', '>=', start_date),
                    ('check_in', '<=', end_date),
                    ('check_in', '>',
                     fields.Datetime.to_string(datetime.combine(start_date, datetime.min.time()) + late_threshold))
                ])

                record.late_count = late_attendances
            else:
                record.late_count = 0

    def action_apply_late_deduction(self):
        managers = set(self.env['hr.employee'].search([('parent_id.department_id.name', '!=', 'RIMS')]).mapped('parent_id.id'))
        # print("manager_partner_ids",manager_partner_ids)
        # managers = self.env['hr.employee'].search([('parent_id', 'in', list(manager_partner_ids))])
        print("managers",managers)
        today = fields.Date.today()

        # Set start date to the 26th of the current month
        previous_month = today.month - 1 if today.month > 1 else 12
        previous_year = today.year - 1 if today.month == 1 else today.year

        # Start date: 26th of previous month
        start_date = datetime(previous_year, previous_month, 26)

        # End date: 27th of current month
        end_date = datetime(today.year, today.month, 20)
        late_threshold = timedelta(hours=9, minutes=15)
        print("----------------\n\n", start_date, end_date)
        if today == end_date.date():

            for manager in managers:
                child = self.env['hr.employee'].search([('parent_id', '=', manager)])
                print("-------manager---\n\n----------", manager)
                root = self.env['hr.late.approval'].create({
                    'employee_id': manager,
                    'state': 'draft',
                    'date_created': today
                })
                print("root", root)
                for record in child:
                    print("------employee----\n\n----------", record.name)
                    late_attendances = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', record.id),
                        ('check_in', '>=', start_date),
                        ('check_in', '<=', end_date),
                        ('check_in', '>',
                         fields.Datetime.to_string(datetime.combine(start_date, datetime.min.time()) + late_threshold))
                    ])
                    print("------late_attendances---", late_attendances)
                    if 1 <= late_attendances <= 3:
                        self.env['hr.late.approval.line'].create({
                            'employee_id': record.id,
                            'late_count': late_attendances,
                            'leave_days': 0,  # Deduct Nothing
                            'late_id': root.id,
                        })

                    elif 4 <= late_attendances <= 6:
                        self.env['hr.late.approval.line'].create({
                            'employee_id': record.id,
                            'late_count': late_attendances,
                            'leave_days': 0.5,  # Deduct half a day
                            'late_id': root.id,
                        })
                    elif late_attendances >= 7:
                        self.env['hr.late.approval.line'].create({
                            'employee_id': record.id,
                            'late_count': late_attendances,
                            'leave_days': 1,  # Deduct full day
                            'late_id': root.id,
                        })

        employees = self.env['hr.employee'].search([])
        for record in employees:
            late_attendances = self.env['hr.attendance'].search_count([
                ('employee_id', '=', record.id),
                ('check_in', '>=', start_date),
                ('check_in', '<=', end_date),
                ('check_in', '>',
                 fields.Datetime.to_string(datetime.combine(start_date, datetime.min.time()) + late_threshold))
            ])
            if 1 <= late_attendances:
                record.action_late_alert()
                print("----------", 13, "----'13'-------\n")

    def action_apply_rims_late_deduction(self):
        managers = self.env['hr.employee'].search([
            ('parent_id.department_id.name', '=', 'RIMS')
        ]).mapped('parent_id.id')
        print("managers", managers)
        # print("manager_partner_ids",manager_partner_ids)
        # managers = self.env['hr.employee'].search([('parent_id', 'in', list(manager_partner_ids))])
        print("managers", managers)
        today = fields.Date.today()

        # Set start date to the 26th of the current month
        previous_month = today.month - 1 if today.month > 1 else 12
        previous_year = today.year - 1 if today.month == 1 else today.year

        # Start date: 26th of previous month
        start_date = datetime(previous_year, previous_month, 26)

        # End date: 27th of current month
        end_date = datetime(today.year, today.month, 20)
        print("----------------\n\n", today, end_date)
        if today == end_date.date():

            for manager in managers:
                child = self.env['hr.employee'].search([('parent_id', '=', manager)])
                print("----------\n\n----------", manager)
                root = self.env['hr.late.approval'].create({
                    'employee_id': manager,
                    'state': 'draft',
                    'date_created': today
                })
                print("root", root)
                for record in child:
                    print("----------\n\n----------", record.name)
                    late_attendances = self.env['hr.employee.shift'].search([
                        ('employee_id', '=', record.id),
                        ('date_start', '>=', start_date),
                        ('date_start', '<=', end_date),
                        ('actual_date_start', '!=', False)
                    ])

                    late_count = sum(1 for shift in late_attendances if
                                     shift.actual_date_start and isinstance(shift.actual_date_start,
                                                                            datetime) and shift.date_start < shift.actual_date_start)
                    print("\nlate_count\n", late_count)

                    # print("------------78977-----------------------\n", b, a)

                    if 1 <= late_count <= 3:
                        print("created\n")
                        self.env['hr.late.approval.line'].create({
                            'employee_id': record.id,
                            'late_count': late_count,
                            'leave_days': 0,
                            'late_id': root.id,
                        })
                    if 4 <= late_count <= 6:
                        self.env['hr.late.approval.line'].create({
                            'employee_id': record.id,
                            'late_count': late_count,
                            'leave_days': 0.5,  # Deduct half a day
                            'late_id': root.id,
                        })
                    elif late_count >= 7:
                        self.env['hr.late.approval.line'].create({
                            'employee_id': record.id,
                            'late_count': late_count,
                            'leave_days': 1,  # Deduct full day
                            'late_id': root.id,
                        })
                    # else:
                    #     root.unlink()

        employees = self.env['hr.employee'].search([])
        for record in employees:
            late_attendances = self.env['hr.employee.shift'].search([
                ('employee_id', '=', record.id),
                ('date_start', '>=', start_date),
                ('date_start', '<=', end_date),
                ('actual_date_start', '!=', False)
            ])

            late_count = sum(1 for shift in late_attendances if
                             shift.actual_date_start and isinstance(shift.actual_date_start,
                                                                    datetime) and shift.date_start < shift.actual_date_start)
            if 1 <= late_count:
                record.action_late_alert()
                print("----------", 13, "----'13'-------\n")




    def get_mail_url(self):
        """Generate URL for employee's attendance records"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
        return f"{base_url}/web#id={self.last_attendance_id.id}&view_type=list&model=hr.attendance"

    def action_late_alert(self):
        """Send separate emails: one to the employee and another to the manager"""

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')

        for record in self:
            if not record.work_email:
                continue  # Skip if employee email is missing

            # Employee's attendance records link
            employee_url = record.get_mail_url()

            # Manager email
            manager = record.parent_id
            manager_email = manager.work_email if manager else False

            # 1. Email to Employee (Only their records)
            employee_mail_values = {
                'subject': _("Late Arrival Warning"),
                'email_to': record.work_email,
                'body_html': """
                    <p>Dear {employee},</p>
                    <p>You have been late <b>{late_count} times</b> this month.</p>
                    <p>Please ensure punctuality to avoid leave deductions.</p>
                    <p>
                        <a href="{employee_url}" 
                           style="display: inline-block; padding: 10px 15px; background-color: #007bff; 
                                  color: white; text-decoration: none; border-radius: 5px;">
                            View Your Attendance Records
                        </a>
                    </p>
                    <p>Regards,<br/>HR Team</p>
                """.format(employee=record.name, late_count=record.late_count, employee_url=employee_url),
            }
            employee_mail = self.env['mail.mail'].create(employee_mail_values)
            employee_mail.sudo().send()

            # Log Message
            record.message_post(body=_("Late arrival warning email sent to %s") % record.name)



            if manager_email:
                # Ensure manager.id is correctly formatted and used
                # domain = [["employee_id.parent_id.id", "=", manager.id], ["is_late_period", "=", True]]
                # domain = [["employee_id.parent_id.id", "=", manager.id]]
                domain = []
                print("*************domain****************",domain)


                # Convert domain list to JSON string and URL encode it
                domain_json = json.dumps(domain)
                encoded_domain = urllib.parse.quote_plus(domain_json)  # Encode special characters
                print("*************encoded_domain****************",encoded_domain)

                # Generate manager’s view URL using Odoo action reference
                action_id = self.env.ref('fnet_late.action_view_late_attendance').id
                manager_view_url = (
                    f"{base_url}/web?#action={action_id}"
                    f"&model=hr.attendance&view_type=list"
                    f"&domain={encoded_domain}"
                )
                print("########manager_view_url########",manager_view_url)

                print("manager_view_url\n....................", manager_view_url)

                manager_mail_values = {
                    'subject': _("Late Arrivals Report for Your Team"),
                    'email_to': manager_email,
                    'body_html': """
                                <p>Dear {manager},</p>
                                <p>The following employees under your supervision have been arriving late this month.</p>
                                <p>
                                    <a href="{manager_view_url}" 
                                       style="display: inline-block; padding: 10px 15px; background-color: #dc3545; 
                                              color: white; text-decoration: none; border-radius: 5px;">
                                        View Team Attendanc*.pywe Records
                                    </a>
                                </p>
                                <p>Regards,<br/>HR Team</p>
                            """.format(manager=manager.name, manager_view_url=manager_view_url),
                }

                manager_mail = self.env['mail.mail'].create(manager_mail_values)
                manager_mail.sudo().send()

                # Log Message print("manager_view_url\n....................", manager_view_url)

                manager.message_post(body=_("Late arrival report email sent to manager %s") % manager.name)


class HrLateApproval(models.Model):
    _name = "hr.late.approval"
    _description = "Late Arrival Approval"

    employee_id = fields.Many2one('hr.employee', string="Manager", required=True)
    late_count = fields.Integer(string="Late Count")
    state = fields.Selection([
        ('draft', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Status", default='draft', required=True)
    leave_days = fields.Float(string="Leave Days")
    late_arrival_report = fields.Binary(string="Late Arrival Report", readonly=True)
    late_arrival_report_name = fields.Char(string="Report Filename", readonly=True)
    late_ids = fields.One2many('hr.late.approval.line', 'late_id', 'Late')
    date_created = fields.Date(string="Created Date", default=fields.Date.today, required=True)
    is_manager = fields.Boolean(string="Approved", compute='_compute_hide_approve')
    is_hide_manager = fields.Boolean()

    def _compute_hide_approve(self):
        for rec in self:
            if self.env.user == rec.employee_id:
                rec.is_manager = True
            else:
                rec.is_manager = False

    #
    @api.model
    def _cron_manager_mail(self):
        if datetime.now().hour == 17 and datetime.now().minute == 0:
            print(1111111111111111111111111111111)
            print(self.is_approved)
            today = datetime.today()

            print(today, '122')
            first_day_of_month = datetime(today.year, today.month, 1)

            print(first_day_of_month, '34444')
            print(today.time())
            if today.day == 4 and today.time() >= time(13, 40):
                pending_approvals = self.search([
                    ('is_approved', '=', False),
                    # ('late_ids.late_count', '<', 0),
                    # ('date_created', '>=', first_day_of_month),
                ])
                print(pending_approvals)
                for record in pending_approvals:
                    mail_values = {
                        'subject': 'Reminder: Pending Approval Required',
                        'body_html': f"""
                                    <p>Dear {record.employee_id.name},</p>
                                    <p>You have pending approvals that require your attention.</p>
                                    <p>Please review and approve the record: <strong>{record.late_ids.employee_id.name}</strong> before 12:00 PM today.</p>
                                    <p></p>
                                    <p>Best Regards,</p>
                                    <p>Your Company</p>
                                """,
                        'email_to': record.employee_id.work_email,
                        'email_from': self.env.user.email or 'noreply@yourcompany.com',
                    }
                    mail = self.env['mail.mail'].create(mail_values)
                    mail.send()

    @api.model
    def cron_hide_approve_button(self):
        today = self.date_created
        print(today)
        yesterday = today - timedelta(day=1)
        print(yesterday)
        records = self.search([('state', '!=', 'approved'),
                               ('date_created', '>', yesterday)])
        if records:
            for rec in records:
                rec.is_hide_manager = True

    def action_approve(self):
        self.state = 'approved'
        for record in self.late_ids:
            if record.is_approved:
                allocation = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('expiry_date', '>', fields.Date.today()),
                    ('holiday_status_id.is_casual', '=', True)
                ], limit=1)

                leave_type = self.env['hr.leave.type'].search([
                    ('is_lop', '=', True)
                ], limit=1)

                if allocation:
                    self.env['hr.leave'].create({
                        'employee_id': record.employee_id.id,
                        'holiday_status_id': allocation.holiday_status_id.id,
                        'request_date_from': fields.Date.today(),
                        'request_date_to': fields.Date.today(),
                        'number_of_days': record.leave_days,
                        'state': 'draft'
                    })
                else:
                    self.env['hr.leave'].create({
                        'employee_id': record.employee_id.id,
                        'holiday_status_id': leave_type.id,
                        'request_date_from': fields.Date.today(),
                        'request_date_to': fields.Date.today(),
                        'number_of_days': record.leave_days,
                        'state': 'draft'
                    })

    def action_reject(self):
        self.write({'state': 'rejected'})

        # def generate_late_arrival_report(self):
        #     file_data = BytesIO()
        #     workbook = xlsxwriter.Workbook(file_data)
        #     sheet = workbook.add_worksheet('Late Arrivals')
        #     date_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'border': 1})
        #
        #     header_format = workbook.add_format({'bold': True, 'bg_color': '#FFC000', 'border': 1})
        #     normal_format = workbook.add_format({'border': 1})
        #
        #     headers = ['Employee ID', 'Employee Name', 'Date', 'Arrival Time', 'Minutes Late', 'LOP Applied (Yes/No)']
        #     for col, header in enumerate(headers):
        #         sheet.write(0, col, header, header_format)
        #
        #     last_week = fields.Date.today() - timedelta(days=7)
        #     # late_attendances = self.env['hr.attendance'].search([('check_in', '>=', last_week)])
        #     late_attendances = self.env['hr.attendance'].search([])
        #
        #     row = 1
        #     for attendance in late_attendances:
        #         minutes_late = max(0, (
        #                     attendance.check_in.hour * 60 + attendance.check_in.minute) - 540)
        #         lop_applied = "Yes" if attendance.employee_id.late_count >= 7 else "No"
        #
        #         print("\n--------", attendance.id, attendance.check_in, attendance.check_in.strftime('%H:%M:%S'), attendance.check_in.date())
        #         sheet.write(row, 0, attendance.employee_id.id, normal_format)
        #         sheet.write(row, 1, attendance.employee_id.name, normal_format)
        #         sheet.write(row, 2, attendance.check_in.date(), date_format)
        #         sheet.write(row, 3, attendance.check_in.strftime('%H:%M:%S'), date_format)
        #         sheet.write(row, 4, minutes_late, normal_format)
        #         sheet.write(row, 5, lop_applied, normal_format)
        #         row += 1
        #
        #     workbook.close()
        #     file_data.seek(0)
        #
        #     file_name = f"Late_Arrival_Report_{fields.Date.today()}.xlsx"
        #     file_content = base64.b64encode(file_data.getvalue())
        #
        #     # Attach report to the record
        #     self.write({
        #         'late_arrival_report': file_content,
        #         'late_arrival_report_name': file_name
        #     })def action_view_late_attendance(self):
        """ Opens hr.attendance records where check-in is after 9 AM for this employee """
        self.ensure_one()
        return {
            'name': "Late Attendance Records",
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance',
            'view_mode': 'tree,form',
            'domain': [
                ('employee_id', '=', self.employee_id.id),
                ('check_in', '>=', fields.Date.today()),  # Filter by today's date
                ('check_in', '>=', fields.Datetime.to_string(fields.Datetime.now().replace(hour=9, minute=0, second=0)))
            ],
            'context': {'default_employee_id': self.employee_id.id},
        }

    #
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': f"/web/content?model=hr.late.approval&id={self.id}&field=late_arrival_report&filename_field=late_arrival_report_name&download=true",
    #         'target': 'self',
    #     }

    def generate_late_arrival_report(self):
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        sheet = workbook.add_worksheet('Late Arrivals')

        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'border': 1})
        time_format = workbook.add_format({'num_format': 'hh:mm:ss', 'border': 1})  # Fix time format
        header_format = workbook.add_format({'bold': True, 'bg_color': '#FFC000', 'border': 1})
        normal_format = workbook.add_format({'border': 1})

        headers = ['Employee ID', 'Employee Name', 'Date', 'Arrival Time', 'Minutes Late', 'LOP Applied (Yes/No)']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        last_week = fields.Date.today() - timedelta(days=7)

        late_attendances = self.env['hr.attendance'].search([('check_in', '>=', last_week)])

        # late_attendances = self.env['hr.attendance'].search([])

        row = 1
        for attendance in late_attendances:
            if not attendance.check_in:
                continue  # Skip records without check-in time

            # Convert check-in time to user's timezone
            check_in_local = fields.Datetime.context_timestamp(self, attendance.check_in)

            # Calculate minutes late (Assuming 9:00 AM threshold)
            minutes_late = max(0, (check_in_local.hour * 60 + check_in_local.minute) - 540)
            lop_applied = "Yes" if attendance.employee_id.late_count >= 7 else "No"

            print("\n--------", attendance.id, check_in_local, check_in_local.strftime('%H:%M:%S'),
                  check_in_local.date())
            sheet.write(row, 0, attendance.employee_id.id, normal_format)
            sheet.write(row, 1, attendance.employee_id.name, normal_format)
            sheet.write(row, 2, check_in_local.date(), date_format)
            sheet.write(row, 3, check_in_local.strftime('%H:%M:%S'), time_format)  # Corrected format
            sheet.write(row, 4, minutes_late, normal_format)
            sheet.write(row, 5, lop_applied, normal_format)
            row += 1

        workbook.close()
        file_data.seek(0)

        file_name = f"Late_Arrival_Report_{fields.Date.today()}.xlsx"
        file_content = base64.b64encode(file_data.getvalue())

        # Attach report to the record
        self.write({
            'late_arrival_report': file_content,
            'late_arrival_report_name': file_name
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content?model=hr.late.approval&id={self.id}&field=late_arrival_report&filename_field=late_arrival_report_name&download=true",
            'target': 'self',
        }


class HrLateApprovalLine(models.Model):
    _name = "hr.late.approval.line"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    late_count = fields.Integer(string="Late Count", compute="_compute_late_count")
    leave_days = fields.Float(string="Leave Days")
    late_id = fields.Many2one('hr.late.approval', string="Late")
    is_approved = fields.Boolean(string="Approved")

    def _compute_late_count(self):
        today = fields.Date.today()
        previous_month = today.month - 1 if today.month > 1 else 12
        previous_year = today.year - 1 if today.month == 1 else today.year

        # Start date: 24th of previous month, End date: 25th of current month
        start_date = datetime(previous_year, previous_month, 26)
        end_date = datetime(today.year, today.month, 21)
        late_threshold = timedelta(hours=9, minutes=15)
        print("\nlate_attendances\n", "11111111111111111111111111111")

        for record in self:
            if record.late_id.employee_id.department_id.name == "RIMS":
                print("RIMS\n")
                if record.employee_id:
                    late_attendances = self.env['hr.employee.shift'].search([
                        ('employee_id', '=', record.employee_id.id),
                        ('date_start', '>=', start_date),
                        ('date_start', '<=', end_date),
                        ('actual_date_start', '!=', False)
                    ])
                    print("late_attendances\n", late_attendances)

                    filtered_shift_ids = late_attendances.filtered(lambda shift:
                                                                   shift.actual_date_start and isinstance(
                                                                       shift.actual_date_start, datetime)
                                                                   and shift.date_start < shift.actual_date_start
                                                                   and not shift.is_regularised
                                                                   ).ids
                    print("filtered_shift_ids:", filtered_shift_ids)

                    record.late_count = len(filtered_shift_ids)
                    if 4 <= len(filtered_shift_ids) <= 6:
                        record.leave_days = 0.5  # Deduct half a day
                    elif len(filtered_shift_ids) >= 7:
                        record.leave_days = 1  # Deduct full day
                    else:
                        record.leave_days = 0

            else:
                if record.employee_id:
                    late_attendances = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', record.employee_id.id),
                        ('check_in', '>=', start_date),
                        ('check_in', '<=', end_date),
                        ('check_in', '>', fields.Datetime.to_string(
                            datetime.combine(start_date, datetime.min.time()) + late_threshold
                        )),
                        ('is_regularised', '=', False)  # Only count unregularized late attendances
                    ])
                    print("\nlate_attendances\n", late_attendances)

                    record.late_count = late_attendances
                    if 4 <= late_attendances <= 6:
                        record.leave_days = 0.5  # Deduct half a day
                    elif late_attendances >= 7:
                        record.leave_days = 1  # Deduct full day
                    else:
                        record.leave_days = 0

    def action_view_late_attendance(self):
        """ Opens hr.attendance records where check-in is after 9:00 AM for this employee """
        self.ensure_one()

        today = fields.Date.today()
        previous_month = today.month - 1 if today.month > 1 else 12
        previous_year = today.year - 1 if today.month == 1 else today.year

        # Start date: 25th of the previous month
        start_date = datetime(previous_year, previous_month, 26)
        end_date = datetime(today.year, today.month, 21)

        if self.late_id.employee_id.department_id.name == "RIMS":
            if self.employee_id:
                late_attendances = self.env['hr.employee.shift'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('date_start', '>=', start_date),
                    ('date_start', '<=', end_date),
                    ('actual_date_start', '!=', False)
                ])
                print("\n late_attendances", late_attendances)

                filtered_shift_ids = late_attendances.filtered(lambda shift:
                                                               shift.actual_date_start and isinstance(
                                                                   shift.actual_date_start, datetime)
                                                               and shift.date_start < shift.actual_date_start
                                                               # and not shift.is_regularised
                                                               ).ids
                print("\n filtered_shift_ids", filtered_shift_ids)

                return {
                    'name': "Late RIMS Attendance Records",
                    'type': 'ir.actions.act_window',
                    'res_model': 'hr.employee.shift',
                    'view_mode': 'tree',
                    'view_id': self.env.ref('fnet_late.hr_shift_late_tree_view').id,
                    'domain': [('id', 'in', filtered_shift_ids)],  # Correct domain format
                    'context': {'default_employee_id': self.employee_id.id},
                }


        else:

            return {
                'name': "Late Attendance Records",
                'type': 'ir.actions.act_window',
                'res_model': 'hr.attendance',
                'view_mode': 'tree',
                'view_id': self.env.ref('fnet_late.hr_attendance_late_tree_view').id,
                # Replace 'your_module' with actual module name
                'domain': [
                    ('employee_id', '=', self.employee_id.id),
                    ('check_in', '>=', start_date),
                    ('check_in', '<=', end_date),
                    ('check_in', '>', fields.Datetime.to_string(
                        datetime.combine(start_date, datetime.min.time()) + timedelta(hours=9, minutes=0)))
                ],
                'context': {'default_employee_id': self.employee_id.id},
            }


class HrAttendanceLate(models.Model):
    _inherit = 'hr.attendance'

    is_regularised = fields.Boolean(string="Regularised")
    reason = fields.Char(string="Reason")
    is_late_period = fields.Boolean(
        string="Is in Late Attendance Period",
        compute="_compute_late_period",
        store=True  # ✅ This must be TRUE for use in domain filters
    )
    #
    # @api.model
    # def _default_manager_employee_id(self):
    #     """Get the employee record of the logged-in user (if they are a manager)."""
    #     employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #     return employee.id if employee else False
    #
    # def open_late_attendance_action(self):
    #     """Return the filtered action dynamically."""
    #     employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #     if not employee:
    #         return {}
    #
    #     return {
    #         'name': "Late Attendance Records",
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'hr.attendance',
    #         'view_mode': 'tree',
    #         'view_id': self.env.ref('fnet_late.hr_attendance_late_tree_view').id,
    #         'domain': [('employee_id.parent_id', '=', employee.id), ('is_late_period', '=', True)],
    #     }
    #
    # @api.model
    # def _search_my_team(self):
    #     employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #     return [('employee_id.parent_id', '=', employee.id)] if employee else []
    #
    # def _search(self, args, offset=0, limit=None, order=None, count=False):
    #     context = self.env.context
    #     if context.get('search_default_my_team'):
    #         args += self._search_my_team()
    #     return super(HrAttendanceLate, self)._search(args, offset, limit, order, count)
    #
    #
    #
    @api.depends('check_in')
    def _compute_late_period(self):
        """Checks if check-in falls within 26-31 of the previous month or 1-25 of the current month and after 09:15 AM."""
        today = fields.Date.context_today(self)
        first_day_of_current_month = today.replace(day=1)
        previous_month_26 = first_day_of_current_month - relativedelta(months=1, day=26)
        previous_month_31 = first_day_of_current_month - timedelta(days=1)
        current_month_25 = first_day_of_current_month + timedelta(days=24)
        late_time = datetime.strptime("09:00:00", "%H:%M:%S").time()

        for record in self:
            if record.check_in:
                check_in_date = record.check_in.date()
                check_in_time = record.check_in.time()

                record.is_late_period = (
                        (previous_month_26 <= check_in_date <= previous_month_31 or
                         first_day_of_current_month <= check_in_date <= current_month_25) and
                        check_in_time > late_time
                )
            else:
                record.is_late_period = False

class HrEmployeeShift(models.Model):
    _inherit = 'hr.employee.shift'

    is_regularised = fields.Boolean(string="Regularised")
    reason = fields.Char(string="Reason")