from datetime import datetime
from dateutil.relativedelta import relativedelta
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError,except_orm

import babel
import base64
import copy
import datetime
import dateutil.relativedelta as relativedelta
import logging
import lxml

from odoo import api, fields, models, tools, _
# from odoo import report as odoo_report
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)



class MailTemplate(models.Model):
    _inherit = "mail.template"

    # def generate_email(self, res_ids, fields=None):
    #     """Generates an email from the template for given the given model based on
    #     records given by res_ids.
    #
    #     :param template_id: id of the template to render.
    #     :param res_id: id of the record to use for rendering the template (model
    #                    is taken from template definition)
    #     :returns: a dict containing all relevant fields for creating a new
    #               mail.mail entry, with one extra key ``attachments``, in the
    #               format [(report_name, data)] where data is base64 encoded.
    #     """
    #     # print 'pppppppppppp', res_ids
    #     self.ensure_one()
    #     multi_mode = True
    #     if isinstance(res_ids, (int, long)):
    #         res_ids = [res_ids]
    #         multi_mode = False
    #     if fields is None:
    #         fields = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date']
    #
    #     res_ids_to_templates = self.get_email_template(res_ids)
    #
    #     # templates: res_id -> template; template -> res_ids
    #     templates_to_res_ids = {}
    #     for res_id, template in res_ids_to_templates.iteritems():
    #         templates_to_res_ids.setdefault(template, []).append(res_id)
    #
    #     results = dict()
    #     for template, template_res_ids in templates_to_res_ids.iteritems():
    #         Template = self.env['mail.template']
    #         # generate fields value for all res_ids linked to the current template
    #         if template.lang:
    #             Template = Template.with_context(lang=template._context.get('lang'))
    #         for field in fields:
    #             Template = Template.with_context(safe=field in {'subject'})
    #             generated_field_values = Template.render_template(
    #                 getattr(template, field), template.model, template_res_ids,
    #                 post_process=(field == 'body_html'))
    #             for res_id, field_value in generated_field_values.iteritems():
    #                 results.setdefault(res_id, dict())[field] = field_value
    #         # compute recipients
    #         if any(field in fields for field in ['email_to', 'partner_to', 'email_cc']):
    #             results = template.generate_recipients(results, template_res_ids)
    #         # update values for all res_ids
    #         for res_id in template_res_ids:
    #             values = results[res_id]
    #             # body: add user signature, sanitize
    #             if 'body_html' in fields and template.user_signature:
    #                 signature = self.env.user.signature
    #                 if signature:
    #                     values['body_html'] = tools.append_content_to_html(values['body_html'], signature, plaintext=False)
    #             if values.get('body_html'):
    #                 values['body'] = tools.html_sanitize(values['body_html'])
    #             # technical settings
    #             #~ print 'rrrrrrrrrrrrrrrrrrrr', template.attachment_ids
    #             values.update(
    #                 mail_server_id=template.mail_server_id.id or False,
    #                 auto_delete=template.auto_delete,
    #                 model=template.model,
    #                 res_id=res_id or False,
    #                 attachment_ids=[attach.id for attach in template.attachment_ids],
    #             )
    #
    #         # Add report in attachments: generate once for all template_res_ids
    #         if template.report_template:
    #             for res_id in template_res_ids:
    #                 attachments = []
    #                 # print '1111111111', res_id
    #                 # print '2222222222', template.report_name
    #                 # print '3333333333', template.model
    #                 if template.model == 'sale.order':
    #                     report_name = self.render_template(template.report_name, template.model, res_id)
    #                     report = template.report_template
    #                     # print '44444444444', report.report_name
    #                     #~ report_service = 'fnet_omega_reportz.report_covering_letterz'
    #                     report_service = report.report_name
    #                     if report.report_name == 'sale.report_saleorder':
    #                         #~ print '5555555555', report.report_service
    #                         if report.report_type in ['qweb-html', 'qweb-pdf']:
    #                             result, format = Template.env['report'].get_pdf([res_id], 'fnet_omega_reportz.report_covering_letter'), 'pdf'
    #                         else:
    #                             result, format = odoo_report.render_report(self._cr, self._uid, [res_id], report_service, {'model': template.model}, Template._context)
    #
    #                         # TODO in trunk, change return format to binary to match message_post expected format
    #                         result = base64.b64encode(result)
    #                         #~ print 'result', result
    #                         # print 'template', template.report_template
    #                         # print 'result', report_service
    #                         if not report_name:
    #                             report_name = 'report.' + report_service
    #                         ext = "." + format
    #                         # print 'rrrrrrrrrrrrrrrrrrrr', report_name
    #                         if not report_name.endswith(ext):
    #                             report_name += ext
    #                         attachments.append((report_name, result))
    #                         #~ print 'rrrrrrrrrrrrrrrrrrrr', attachments
    #                         results[res_id]['attachments'] = attachments
    #                 else:
    #                     report_name = self.render_template(template.report_name, template.model, res_id)
    #                     report = template.report_template
    #                     report_service = report.report_name
    #                     if report.report_type in ['qweb-html', 'qweb-pdf']:
    #                         result, format = Template.env['report'].get_pdf([res_id], report_service), 'pdf'
    #                     else:
    #                         result, format = odoo_report.render_report(self._cr, self._uid, [res_id], report_service, {'model': template.model}, Template._context)
    #
    #                     # TODO in trunk, change return format to binary to match message_post expected format
    #                     result = base64.b64encode(result)
    #                     #~ print 'result', result
    #                     # print 'template', template.report_template
    #                     # print 'result', report_service
    #                     if not report_name:
    #                         report_name = 'report.' + report_service
    #                     ext = "." + format
    #                     if not report_name.endswith(ext):
    #                         report_name += ext
    #                     attachments.append((report_name, result))
    #                     results[res_id]['attachments'] = attachments
    #
    #
    #     return multi_mode and results or results[res_ids[0]]
