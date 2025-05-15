from odoo import http
from odoo.http import request
import base64
from time import gmtime, strftime


class EmployeeRegistration(http.Controller):

    @http.route('/joining_date_proposed/check', type='json', auth='public')
    def joining_date_check(self, expected_joining_date, joining_date_proposed):
        if expected_joining_date < joining_date_proposed:
            return True
        return False

    @http.route("/register_form/<model('employee.registration'):id>/<string:access_token>", type='http',
                auth="public", website=True)
    def page_employee_single(self, id, access_token=None):

        employee_details = request.env['employee.registration'].sudo().search(
            [('id', '=', id.id)])
        current_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        expire_date = employee_details.document_url_expire.strftime("%Y-%m-%d %H:%M:%S")
        if employee_details.access_token == access_token and expire_date > current_date:
            print(employee_details.access_token)
            select_state_id = request.env['res.country.state'].sudo().search([])
            select_country_id = request.env['res.country'].sudo().search([])

            values = {
                'states': select_state_id,
                'countries': select_country_id,
                'single_employee': employee_details,
                'error': {},
            }

            return http.request.render("employee_documents.employee_details_list", values)
        else:
            return request.render("employee_documents.permission_denied")

    def _prepare_employee_data(self, post):
        file = post.get('upload_file')
        return {
            'date': post.get('date', False),
            'email': post.get('email', False),
            # 'web_enter_name': post.get('name', False),
            'fathers_name': post.get('fathers_name', False),
            'mothers_name': post.get('mothers_name', False),
            'blood_group': post.get('blood_group', False),
            'contact_number': post.get('contact_number', False),
            'emergency_contact_number': post.get('emg_contact_number', False),
            'street': post.get('street', False),
            'street2': post.get('street2', False),
            'zip': post.get('zip', False),
            'city': str(post.get('city', False)),
            'p_street': post.get('p_street', False),
            'p_street2': post.get('p_street2', False),
            'p_zip': post.get('p_zip', False),
            'p_city': post.get('p_city', False),
            'total_previous_ctc': post.get('total_previous_ctc', False),
            'state_id': post.get('select_state', False) or False,
            'country_id': post.get('select_country', False) or False,
            'p_state_id': post.get('p_select_state', False) or False,
            'p_country_id': post.get('p_select_country', False) or False,
            'no_of_year_experience': post.get('experience', False),
            'joining_date_proposed': post.get('joining_date_proposed', False),
            # 'expected_joining_date': post.get('expected_joining_date', False),
            'gender': post.get('gender', False),
            'date_of_birth': post.get('date_of_birth', False),
            'previous_designation': post.get('previous_designation', False),
            'marital': post.get('marital', False),
            'certificate': post.get('certificate', False),
            'study_field': post.get('study_field', False),
            # 'visa_no': post.get('visa_no', False),
            'passport_id': post.get('passport_id', False),
            'pf_number': post.get('pf_number', False),
            'uan_number': post.get('uan_number', False),
            'aadhar_number': post.get('aadhar_number', False),
            'pan_number': post.get('pan_number', False),
            'esi_number': post.get('esi_number', False),
            'consolidated_pay': post.get('consolidated_pay', False),
        }

    @http.route(['/confirmation'], type='http', auth='public', website=True)
    def employee_data_confirmation(self, redirect=None, **post):
        print(id)
        employee_vals = self._prepare_employee_data(post)
        print(employee_vals)
        employee_register_obj = request.env['employee.registration'].sudo().browse(
            int(post.get('employee_register_id')))
        employee_register_obj.write(employee_vals)

        if post.get('aadhar_card', False):
            file = post.get('aadhar_card')
            attachment_ids = request.env['ir.attachment'].sudo().create({
                'name': post.get('aadhar_card').filename,
                'datas': base64.b64encode(file.read()),
                'type': 'binary',
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('aadhar_card').filename,
                'file_name': "Aadhar Card"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids.id)]})

        # employee_register_obj.sudo(2).message_post(body="Aadhar Card", attachment_ids=[attachment_ids.id])

        if post.get('pan_card', False):
            file = post.get('pan_card')
            attachment_ids_pan = request.env['ir.attachment'].sudo().create({
                'name': post.get('pan_card').filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('pan_card').filename,
                'file_name': "Pan Card"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids_pan.id)]})

            # employee_register_obj.sudo(2).message_post(body="Pan Card", attachment_ids=[attachment_ids_pan.id])
        if post.get('photo', False):
            file = post.get('photo')
            attachment_ids_photo = request.env['ir.attachment'].sudo().create({
                'name': post.get('photo').filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('photo').filename,
                'file_name': "Photo"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids_photo.id)]})

        if post.get('employment_form', False):
            file = post.get('employment_form')
            attachment_ids = request.env['ir.attachment'].sudo().create({
                'name': post.get('employment_form').filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('employment_form').filename,
                'file_name': "Employment Form"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids.id)]})

        if post.get('tenth_marksheet', False):
            file = post.get('tenth_marksheet')
            attachment_ids = request.env['ir.attachment'].sudo().create({
                'name': post.get('tenth_marksheet').filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('tenth_marksheet').filename,
                'file_name': "10th Mark sheet"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids.id)]})
        if post.get('twelfth_marksheet', False):
            file = post.get('twelfth_marksheet')
            attachment_ids = request.env['ir.attachment'].sudo().create({
                'name': post.get('twelfth_marksheet').filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('twelfth_marksheet').filename,
                'file_name': "12th Mark sheet"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids.id)]})
        if post.get('degree_certificate', False):
            file = post.get('degree_certificate')
            attachment_ids = request.env['ir.attachment'].sudo().create({
                'name': post.get('degree_certificate').filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('degree_certificate').filename,
                'file_name': "Degree sheet"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids.id)]})
        if post.get('consolidated_marksheet', False):
            file = post.get('consolidated_marksheet')
            attachment_ids = request.env['ir.attachment'].sudo().create({
                'name': post.get('consolidated_marksheet').filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('consolidated_marksheet').filename,
                'file_name': "Consolidated Mark Sheet"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids.id)]})
        if post.get('payslips', False):
            file = post.get('payslips')
            attachment_ids = request.env['ir.attachment'].sudo().create({
                'name': post.get('payslips').filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('payslips').filename,
                'file_name': "Payslips"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids.id)]})
        if post.get('bank_statement', False):
            file = post.get('bank_statement')
            attachment_ids = request.env['ir.attachment'].sudo().create({
                'name': post.get('bank_statement').filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('bank_statement').filename,
                'file_name': " Bank Statement"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids.id)]})
        if post.get('reliving_letter', False):
            file = post.get('reliving_letter')
            attachment_ids = request.env['ir.attachment'].sudo().create({
                'name': post.get('reliving_letter').filename,
                'datas': base64.b64encode(file.read()),
                'res_model': 'employee.registration',
                'res_id': employee_register_obj and employee_register_obj.id,
                'res_name': post.get('reliving_letter').filename,
                'file_name': "Reliving Letter"
            })
            employee_register_obj.write({'document_ids': [(4, attachment_ids.id)]})

        # educational Qualifications
        if post.get('pg_institute_name', False):
            educational_ids = request.env['employee.education.qualification'].sudo().create({
                'name_of_the_institute': post.get('pg_institute_name', False),
                'dept_name': post.get('pg_course'),
                'course_type': 'pg',
                'marks': post.get('pg_marks', False),
            })
            employee_register_obj.write({'education_qualif_ids': [(4, educational_ids.id)]})

        if post.get('ug_institute_name', False):
            educational_ids = request.env['employee.education.qualification'].sudo().create({
                'name_of_the_institute': post.get('ug_institute_name', False),
                'dept_name': post.get('ug_course'),
                'course_type': 'ug',
                'marks': post.get('ug_marks', False),
            })
            employee_register_obj.write({'education_qualif_ids': [(4, educational_ids.id)]})
        if post.get('twelfth_institute_name', False):
            educational_ids = request.env['employee.education.qualification'].sudo().create({
                'name_of_the_institute': post.get('twelfth_institute_name', False),
                'dept_name': post.get('twelfth_course'),
                'course_type': 'other_course',
                'marks': post.get('twelfth_marks', False),
            })
            employee_register_obj.write({'education_qualif_ids': [(4, educational_ids.id)]})

        if post.get('tenth_institute_name', False):
            educational_ids = request.env['employee.education.qualification'].sudo().create({
                'name_of_the_institute': post.get('tenth_institute_name', False),
                'dept_name': post.get('tenth_course'),
                'course_type': 'other_course',
                'marks': post.get('tenth_marks', False),
            })
            employee_register_obj.write({'education_qualif_ids': [(4, educational_ids.id)]})
        if post.get('add_institute_name', False):
            educational_ids = request.env['employee.education.qualification'].sudo().create({
                'name_of_the_institute': post.get('add_institute_name', False),
                'dept_name': post.get('add_course'),
                'course_type': 'other_course',
                'marks': post.get('add_marks', False),
            })
            employee_register_obj.write({'education_qualif_ids': [(4, educational_ids.id)]})
        if post.get('add2_institute_name', False):
            educational_ids = request.env['employee.education.qualification'].sudo().create({
                'name_of_the_institute': post.get('add2_institute_name', False),
                'dept_name': post.get('add2_course'),
                'course_type': 'other_course',
                'marks': post.get('add2_marks', False),
            })
            employee_register_obj.write({'education_qualif_ids': [(4, educational_ids.id)]})

        values = {
            'error': {},
        }

        template_obj = request.env['mail.mail']
        template_data = {
            'subject': employee_register_obj.name + ' Document Submitted',
            'body_html': "<p>Dear Sir/Madam,</p><p>Please find the document " + employee_register_obj.name + " has been submitted </p><br></br><p>Thanks & Regards</p><p>Admistration</p>",
            'email_from': 'odoo@futurenet.in',
            'email_to': 'hr@futurenet.in'
        }
        template_id = template_obj.sudo(2).create(template_data)
        template_obj.sudo(2).send(template_id)
        template_id.sudo(2).send()
        return request.render("employee_documents.confirmation", values)
