from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.addons.survey.controllers.main import Survey
import logging

_logger = logging.getLogger(__name__)


class SurveyExtended(Survey):

    @http.route('/survey/submit/<string:survey_token>/<string:answer_token>', type='json', auth='public', website=True)
    def survey_submit(self, survey_token, answer_token, **post):
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        questions, page_or_question_id = survey_sudo._get_survey_questions(answer=answer_sudo,
                                                                           page_id=post.get('page_id'),
                                                                           question_id=post.get('question_id'))
        if questions and questions.is_name:
            answer_sudo.user_name = post.get(str(page_or_question_id))
        if questions and questions.validation_email:
            answer_sudo.survey_email = post.get(str(page_or_question_id))
            answer_sudo.send_otp_email()
        # if questions.answer_sudo.state == 'done':
        #     answer_sudo.session_end_result_mail()
        if questions and questions.is_otp:
            if post.get(str(page_or_question_id)) != '' and post.get(str(page_or_question_id)) != answer_sudo.otp_code:
                return {
                    'error': 'validation',
                    'message': _("Your OTP is incorrect. Please refresh the page and enter the correct OTP."),
                    'fields': {str(page_or_question_id): _("Invalid OTP")}
                }
            else:
              return super(SurveyExtended, self).survey_submit(survey_token, answer_token, **post)
        else:
            return super(SurveyExtended, self).survey_submit(survey_token, answer_token, **post)
