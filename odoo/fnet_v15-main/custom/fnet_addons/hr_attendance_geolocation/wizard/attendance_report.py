# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from geopy.distance import great_circle as GC
import requests
import json
from datetime import datetime, timedelta, time
import xlsxwriter
from io import StringIO
import base64
import pytz
from odoo.exceptions import UserError, ValidationError


def to_utc_naive(datetime, record):
    user_tz = record._context.get('tz') or self.env.user.tz
    local = pytz.timezone(user_tz)
    return pytz.utc.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(local).replace(tzinfo=None)


class AttendanceReportWizard(models.TransientModel):
    _name = 'attendance.report'
    _description = 'Attendance Report'

    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    work_location = fields.Many2one('hr.work.location', string="Location")
    distance = fields.Float(string='Range Out of(km)')
    auto_check_out = fields.Boolean('Automatic Check out')
    location_latitude = fields.Float("Location Latitude", digits="Location", compute='_compute_location')
    location_longitude = fields.Float("Location Longitude", digits="Location", compute='_compute_location')
    location_url = fields.Char("Location URL", compute='_compute_location')
    filedata = fields.Binary('Download file', readonly=True)
    filename = fields.Char('Filename', size=64, readonly=True)

    @api.depends('work_location')
    def _compute_location(self):
        for rec in self:
            if not rec.company_id.enable_geolocation:
                raise UserError(_("Enable GeoLocation in Settings"))
            if rec.work_location:
                if rec.work_location.location_latitude and rec.work_location.location_longitude:
                    rec.location_latitude = rec.work_location.location_latitude
                    rec.location_longitude = rec.work_location.location_longitude
                    rec.location_url = 'https://maps.google.com/?q=%s,%s' % (rec.location_latitude, rec.location_longitude)
                else:
                    rec.location_latitude = ''
                    rec.location_longitude = ''
                    rec.location_url = ''
            else:
                rec.location_latitude = ''
                rec.location_longitude = ''
                rec.location_url = ''

            # address = rec.company_id.name + ' ' + rec.company_id.street2 + ' ' + rec.company_id.city + ' ' + ' ' + rec.company_id.zip
            # parameters = {
            #     'key': rec.company_id.api_key,
            #     'location': address,
            # }
            # response = requests.get("http://www.mapquestapi.com/geocoding/v1/address", params=parameters)
            # data = json.loads(response.text)['results']
            # lat = data[0]['locations'][0]['latLng']['lat']
            # lng = data[0]['locations'][0]['latLng']['lng']
            # if lat and lng:
            #     rec.company_latitude = lat
            #     rec.company_longitude = lng
            #     rec.company_location = 'https://maps.google.com/?q=%s,%s' % (rec.company_latitude, rec.company_longitude)
            # else:
            #     rec.company_latitude = ''
            #     rec.company_longitude = ''
            #     rec.company_location = ''

    def generate_excel_report(self):
        output = StringIO()
        url = '/tmp/'
        workbook = xlsxwriter.Workbook(url + 'Attendance Report.xlsx', {'remove_timezone': True})
        worksheet = workbook.add_worksheet()

        merge_format1 = workbook.add_format(
            {'bold': 1, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'font_name': 'Liberation Serif', })
        merge_format2 = workbook.add_format(
            {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'underline': 'underline',
             'font_name': 'Liberation Serif', })
        merge_format3 = workbook.add_format({'border': 1, 'align': 'left', 'font_name': 'Liberation Serif'})
        merge_format4 = workbook.add_format(
            {'border': 1, 'align': 'left', 'font_name': 'Liberation Serif', 'num_format': 'd-m-yyyy hh:mm:ss'})
        merge_format5 = workbook.add_format(
            {'border': 1, 'align': 'left', 'font_name': 'Liberation Serif', 'num_format': '#,##0,0.00'})
        merge_format6 = workbook.add_format({'border': 1, 'align': 'center', 'font_name': 'Liberation Serif'})
        merge_format7 = workbook.add_format(
            {'border': 1, 'align': 'center', 'font_name': 'Liberation Serif', 'bg_color': '#D3D3D3', 'text_wrap': True})

        worksheet.set_column('A:A', 7)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:G', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)
        worksheet.merge_range('A1:E1', self.company_id.name, merge_format1)
        worksheet.merge_range('A2:E2', 'ATTENDANCE REPORT', merge_format1)
        worksheet.merge_range('A3:E3',
                              str(self.date_from).split('-')[2] + '-' + str(self.date_from).split('-')[1] + '-' +
                              str(self.date_from).split('-')[0] + ' to ' + str(self.date_to).split('-')[2] + '-' +
                              str(self.date_to).split('-')[1] + '-' + str(self.date_to).split('-')[0], merge_format1)
        worksheet.write('A5', "S.No", merge_format7)
        worksheet.write('B5', "Employee Name", merge_format7)
        worksheet.write('C5', "Department", merge_format7)
        worksheet.write('D5', "Check In", merge_format7)
        worksheet.write('E5', "Check-In Distance(km)", merge_format7)
        worksheet.write('F5', "Check Out", merge_format7)
        worksheet.write('G5', "Check Out Distance(km)", merge_format7)
        worksheet.write('H5', "Automatic Check Out", merge_format7)

        location_coordinates = [self.location_latitude, self.location_longitude]
        final_attendances = []
        attendances = []
        domain = [('work_location_id', '=', self.work_location.id), ('check_in', '>=', datetime.combine(self.date_from, time.min)),
                  ('check_out', '<=', datetime.combine(self.date_to, time.max))]
        if self.auto_check_out:
            domain.append(('automatic_checkout', '=', True))
        print("---", domain, "--domain--")
        attendances += self.env['hr.attendance'].search(domain)
        for att in attendances:
            checkin_coordinates = [att.check_in_latitude, att.check_in_longitude]
            checkout_coordinates = [att.check_out_latitude, att.check_out_longitude]
            checkin_distance = GC(location_coordinates, checkin_coordinates)
            checkout_distance = GC(location_coordinates, checkout_coordinates)
            checkin_distance = round(float(str(checkin_distance).split(' ')[0]), 2)
            checkout_distance = round(float(str(checkout_distance).split(' ')[0]), 2)
            if checkin_distance > self.distance or checkout_distance > self.distance:
                final_attendances.append({'id': att, 'checkin_distance': str(checkin_distance), 'checkout_distance': str(checkout_distance)})
        n = 6
        c = 1
        for attendance in final_attendances:
            worksheet.write('A' + str(n), str(c), merge_format6)
            worksheet.write('B' + str(n), attendance['id'].employee_id.name, merge_format4)
            worksheet.write('C' + str(n), attendance['id'].employee_id.department_id.display_name if attendance['id'].employee_id.department_id else '', merge_format4)
            worksheet.write('D' + str(n), to_utc_naive(attendance['id'].check_in, attendance['id']) if attendance['id'].check_in else '', merge_format4)
            worksheet.write_url('E' + str(n), attendance['id'].check_in_location, string=str(attendance['checkin_distance']) + ' km' if attendance['id'].check_in_location else '')
            worksheet.write('F' + str(n), to_utc_naive(attendance['id'].check_out, attendance['id']) if attendance['id'].check_out else '', merge_format4)
            worksheet.write_url('G' + str(n), attendance['id'].check_out_location, string=attendance['checkout_distance'] + ' km' if attendance['id'].check_out_location else '')
            worksheet.write('H' + str(n), '☑' if attendance['id'].automatic_checkout else '☐', merge_format6)
            n = n + 1
            c = c + 1

        workbook.close()
        fo = open(url + 'Attendance Report.xlsx', "rb+")
        data = fo.read()
        out = base64.encodebytes(data)
        filename = 'Attendance Report(%s).xlsx' % (self.date_from.strftime('%d %B %Y') + ' ' + '-' + ' ' + self.date_to.strftime('%d %B %Y'))
        self.write({'filedata': out, 'filename': filename})
        return {
                'name': 'Attendance Report',
                'res_model': 'attendance.report',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'nodestroy': True,
                'res_id': self.id
                }
