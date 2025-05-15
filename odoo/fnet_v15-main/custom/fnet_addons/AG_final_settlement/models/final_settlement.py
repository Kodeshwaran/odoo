# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta ,date
from dateutil import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError
import math


class FinalSettlement(models.Model):
	_name = "final.settlement"
	_rec_name = 'employee_id'


	def generate_exit_form(self):
		exit_form = self.env['exit.interview'].create({
				'settlement_id': self.id,
				'name': self.employee_id.id,
				'employeeid': self.employee_id.employeeid,
				'reporting_manager': self.employee_id.parent_id.id,
				'department': self.department_id.id,
				'date_of_resignation': self.resign_date,
			})
		url = '/mail/view?model=exit.interview&res_id=%s' % (exit_form.id)
		mail_content = "  Dear  <strong>" + self.employee_id.name + "</strong>, <br/>As part of our relieving process, we kindly request you to complete the Exit Interview Form."\
																	 " Your feedback is highly valuable to us" \
																	 " and will help us improve our workplace for current and future employees."\
																	"Please click the button below to fill out the form:<br/><br/>" \
																	"<a href=%s><button class='GFG'>Click Here to Fill Out the Exit Interview Form</button></a>" % url
		main_content = {
			'subject': 'Exit Interview Form',
			'email_from': self.env.user.company_id.email,
			'body_html': mail_content,
			'email_to': self.employee_id.work_email
		}
		self.env['mail.mail'].sudo().create(main_content).send()

	def generate_no_due(self):
		no_due = self.env['no.due'].create({
			'settlement_id': self.id,
			'name': self.employee_id.id,
			'employeeid': self.employee_id.employeeid,
			'manager': self.employee_id.parent_id.id,
			'select_department': self.department_id.id,
			'date_join': self.join_date,
			'date_of_resignation': self.resign_date,
		})
		url = '/mail/view?model=no.due&res_id=%s' % (no_due.id)
		mail_content = "  Dear  <strong>" + self.employee_id.name + "</strong>, <br/>Click on the button below to submit the No Due Form." \
																	"Do it as soon as possible.<br/><br/>" \
																	"<a href=%s><button>View No Due</button></a>" % url
		main_content = {
			'subject': 'No Due Form',
			'email_from': self.env.user.company_id.email,
			'body_html': mail_content,
			'email_to': self.employee_id.work_email
		}
		self.env['mail.mail'].sudo().create(main_content).send()
	#
	def action_generate(self):
		payable = 0
		recievable = 0
		unpaid_tot = 0
		leave_tot = 0
		tot = 0
		working_days = 0
		amount = 0
		days_in_year = 365
		months_in_year = 12

		for obj in self:
			final_settlement = obj.settlement_type_id.final_settlement
			leave_pending = obj.employee_id.leaves_count
			joining_date = obj.join_date

			holiday_ids = self.env['hr.leave'].search([('employee_id','=',obj.employee_id.id),('holiday_status_id','=',4),('state','not in',('cancel','refuse'))])
			for holiday in holiday_ids:
				holiday_obj = self.env['hr.leave'].browse(holiday).id
				unpaid_tot = unpaid_tot + holiday_obj.number_of_days

			# holiday_leave_ids = self.env['hr.leave.allocation'].search([('employee_id', '=', obj.employee_id.id)])
			# for holiday in holiday_leave_ids:
			# 	day_obj = self.env['hr.leave.allocation.accrual.calculator'].browse(holiday).id
			# 	leave_tot = leave_tot + day_obj.balance

			# gratuity_ids = self.env['gratuity.employee'].search([('gratuity_line_id', '=', obj.gratuity_line_id.id)])
			# for gratuity_id in gratuity_ids:
			# 	gratuity_obj = self.env['gratuity.employee'].browse(gratuity_id).id
			# 	if gratuity_obj.resign_amount:
			# 		final_due_amt = gratuity_obj.resign_amount
			# 	else:
			# 		final_due_amt = gratuity_obj.termination_amount
			#
			date_to = obj.resign_date
			if date_to:
				date_to = datetime.strptime(str(date_to),"%Y-%m-%d")
			if joining_date:
				joining_date = datetime.strptime(str(joining_date),"%Y-%m-%d")
			if not (date_to and joining_date):
				raise UserError(_('make sure joining_date and document date given'))

			working_days = ((date_to - joining_date).days + 1) - unpaid_tot
			allow_rules = []
			employee_id = obj.employee_id and obj.employee_id.id
			contract_ids = self.env['hr.contract'].search([('employee_id','=',employee_id),('state','=','open')])
			if not contract_ids:
				raise UserError(_('no active contract for this employee'))
			contract_id = contract_ids[0]
			contract_obj = self.env['hr.contract'].browse(contract_id).id
			basic = contract_obj.wage * contract_obj.basic_percentage
			net = contract_obj.wage
			# contract_type_id = contract_obj.contract_type
			total_sal = contract_obj.wage * contract_obj.basic_percentage
			#contract_lines = contract_obj.hr_allowance_line_ids
			# for l in contract_lines:
			# 	if not 'CV' in l.code:
			# 		tot = tot + l.amt
			# self.fs_gross_per_day = (total_sal/30)


			# leave_balance_ids = self.env['n2n.leave.analysis.view'].search([('employee_id','=',employee_id)])
			# leave_bal_id = leave_balance_ids[0]
			# leave_bal_obj = self.env['n2n.leave.analysis.view'].browse(leave_bal_id).id
			# leave_balances = leave_bal_obj.leave_amt

			# var_gross = net
			#
			# self.fs_gross_per_day = var_gross / days_in_year * months_in_year  ####### gross per day for leave


			# leave_records = self.env['hr.leave'].search([('employee_id','=',employee_id),('state', '=', 'validate'),('holiday_status_id','=',1)], order='date_to desc',
			# 											limit=1)
			#
			# lv = leave_records
			# self.last_vacation = lv.date_to
			# print('-----------last vacation-------', self.last_vacation)

			# for al_line in contract_obj.xo_allowance_rule_line_ids:
			# #     al_line.copy({'od_sett_id':ids[0],'contract_id':False})
			# payroll_ids = self.env['hr.salary.sheet.view'].search([('employee_id', '=', employee_id)],order='date_to desc',limit=1)
			# if payroll_ids:
			# 	payroll_obj = payroll_ids[-1:]
			# 	pay_overtime = payroll_obj.ot_allowance
			# 	pay_add = payroll_obj.additions
			# 	pay_ded = payroll_obj.deductions
			# 	pay_allw = payroll_obj.allowances_value
			# 	pay_net_sal = payroll_obj.net_salary
			# payroll_id = payroll_ids[0]
			#payroll_obj = self.env['hr.salary.sheet.view'].browse(payroll_id).id


			vals = {'basic':basic,
					# 'contract_type_id':contract_type_id,
					# 'join_date':obj.employee_id.join_date,
					'total_salary':total_sal,
					#'leave_pending':leave_tot,
					#'unpaid_leaves':unpaid_tot,
					#'leave_pending_balance':leave_balances,
					'total_working_days':working_days,
					# 'job_id':obj.employee_id.job_id.id,
					# 'department_id':obj.employee_id.department_id.id,
					'is_generated': True,
					}
			self.write(vals)

			# partner_id = obj.employee_id.address_home_id.id
			# settlement_type_id = obj.settlement_type_id and obj.settlement_type_id.id
			# settlement_ids = self.env['final.settlement.type.master'].search([('id','=',settlement_type_id)])
			# settlement_type_obj = self.env['final.settlement.type.master'].browse(settlement_ids).id
			# account_ids = []
			# for accounts in settlement_type_obj.settlement_type_master_line:
			# 	account_ids.append(accounts.account_id.id)
			# if not account_ids:
			# 	raise UserError(_('first set the accounts in settlement type master'))
			# # if not partner_id:
			# #     raise osv.except_osv(_('Error!'), _('define Home Address First'))
			# if obj.account_line:
			# 	for lines in obj.account_line:
			# 		self.env['final.settlement.account.line'].unlink()


			# account_move_line_obj = self.env['account.move.line']



			# move_ids = account_move_line_obj.search([('partner_id','=',partner_id),('account_id','in',account_ids)])
			# if not move_ids:
			# 	raise UserError(_('there is no accounting entries for the particular employee'))

			# move_data = account_move_line_obj.browse(move_ids).id
			# move_line_credit={}
			# move_line_debit={}
			# for line in move_data:
			# 	if not line.account_id:
			# 		continue
			# 	if line.credit:
			# 		move_line_credit[line.account_id.id] = (line.account_id.id not in move_line_credit) \
			# 												 and line.credit or (float(move_line_credit.get(line.account_id.id))+line.credit)
			# 	if line.debit:
			# 		move_line_debit[line.account_id.id] = (line.account_id.id not in move_line_debit) \
			# 											   and line.debit or (float(move_line_debit.get(line.account_id.id))+line.debit)

			# result =  { k: move_line_debit.get(k, 0) - move_line_credit.get(k, 0) for k in set(move_line_debit) | set(move_line_credit) }
			# for account_id in result:
			# 	if result[account_id] < 0:
			# 		payable = math.fabs(result[account_id])
			# 		amount = math.fabs(result[account_id])
			# 	elif result[account_id] >0:
			# 		amount = (-1 * result[account_id])
			# 		payable = 0


			# 	vals = {
			# 		'account_id':account_id,
			# 		'balance':result[account_id],
			# 		'account_line_id':self.id,
			# 		'amount':amount,
			# 		'final_settlement_flag':final_settlement

			# 	}
			# 	self.env['final.settlement.account.line'].create(vals)
		# self.write(cr,uid,ids,{'checking_acc_entry_button_ctrl':True})
		return True

	def action_submit(self):
		if not self.is_generated:
			raise ValidationError("Kindly generate the salary details")
		if not self.is_gratuity_calculated:
			raise ValidationError("Kindly generate the Gratuity Calculation")
		if not self.is_final_dues_generated:
			raise ValidationError("Kindly generate the Final Dues")
		self.write({'state': 'submit'})

	def action_approve(self):
		self.write({'state': 'approve'})

	#
	def action_final_settlement(self):
		final_due_amt = 0
		final_pay = 0

		for obj in self:
			receivable_acc_id = obj.employee_id.address_id.property_account_receivable_id and obj.employee_id.address_id.property_account_receivable_id.id
			payable_acc_id = obj.employee_id.address_id.property_account_payable_id and obj.employee_id.address_id.property_account_payable_id.id
			if not payable_acc_id:
				raise UserError(_('set payable acc in employee home address'))
			if not receivable_acc_id:
				raise UserError(_('set recievable acc in employee home address'))
			for lines in obj.gratuity_line_id:
				if not lines:
					raise UserError(_('there is no lines in gratuity'))
				if lines.resign_amount:
					final_due_amt = lines.resign_amount
				elif lines.termination_amount:
					final_due_amt = lines.termination_amount

			final_pay = final_due_amt + obj.other_earnings - obj.other_deductions

			vals = {
				'final_settlement_amount': final_due_amt,
				'final_payment': final_pay,
				}
			self.write(vals)
			lines = [(5, 0, 0)]
			if obj.final_payment < 0:
				vals = {
						'account_id': receivable_acc_id,
						'account_line_id':obj.id,
						'amount': final_pay,
						'balance': -1 * final_pay,
						'final_settlement_flag':obj.settlement_type_id.final_settlement
					}
				lines.append((0, 0, vals))
				obj.account_line = lines
			if obj.final_payment >= 0:
				vals = {
					'account_id': payable_acc_id,
					'account_line_id': obj.id,
					'amount': final_pay,
					'balance': -1 * final_pay,
					'final_settlement_flag': obj.settlement_type_id.final_settlement
				}
				lines.append((0, 0, vals))
				obj.account_line = lines
			self.is_final_dues_generated = True
			return True

	@api.depends('resign_date', 'join_date', 'last_vacation', 'fs_gross_per_day', 'employee_id')
	def action_fs_date_diff(self):
		d3 = self.join_date
		d4 = self.resign_date
		# total_leave_allocation = 0
		# total_leave_taken = 0
		# leaves = self.env['hr.leave.type'].search([('allow_encashment', '=', True)])
		# leaves_allocation = self.env['hr.leave.allocation'].search([('holiday_status_id', 'in', leaves.ids),
		# 															('state', '=', 'validate'),
		# 															('employee_id', '=', self.employee_id.id)])
		# for leave_all in leaves_allocation:
		# 	total_leave_allocation += leave_all.number_of_days_display
		# leave_taken = self.env['hr.leave'].search([('holiday_status_id', 'in', leaves.ids),
		# 															('state', '=', 'validate'),
		# 															('employee_id', '=', self.employee_id.id)])
		# for leave_take in leave_taken:
		# 	total_leave_taken += leave_take.number_of_days
		#
		# if total_leave_allocation:
		# 	self.available_days = total_leave_allocation - total_leave_taken
		self.fs_gross_available_days = self.fs_gross_per_day * self.available_days
	#
	#d5 = self.last_vacation
		days_in_year = 365
		months_in_year = 12
		leaves_per_month = 2.5
		days_in_month = 30
		bal_leave = 0.0
		if d3 and d4:
			d3 = datetime.strptime(str(d3), "%Y-%m-%d")
			d4 = datetime.strptime(str(d4), "%Y-%m-%d")

			# r2 relativedelta ----->   relativedelta(years=+1, months=+11, days=+30)
			r2 = relativedelta.relativedelta(d4, d3)
			print('--------------------r2--------------', r2)
			self.fs_temp_year = r2.years
			print('--------------------fs_tmp_yr--------------', self.fs_temp_year)
			# self.fs_temp_day = r2.days+(r2.months*days_in_month)
			self.fs_temp_day = (d4 - (d3 + relativedelta.relativedelta(years=r2.years))).days + 1
			print('--------------------fsday_tmp_--------------', self.fs_temp_day)
			self.fs_total_period = str(self.fs_temp_year) + ' year(s) ' + str(self.fs_temp_day) + ' day(s)'
			print('--------------------fs_total_period--------------', self.fs_total_period)

			# if d5:
			# 	d5 = datetime.strptime(str(d5), '%Y-%m-%d %H:%M:%S')
			# 	r3 = relativedelta.relativedelta(d4, d5)
			# 	print('------------R3------------', r3)
			# 	print('--------D5-----------',d5)
			# 	print('----------D4------',d4)
			# 	self.fs_temp_month_2 = r3.months + (r3.years * months_in_year)
			# 	print('------------fs_temp_month_2------------', self.fs_temp_month_2)
			# 	fs_temp_day2 = (r3.days+1)*leaves_per_month/days_in_month
			# 	print('------------fs_temp_day2------------', fs_temp_day2)
			# 	self.available_days = (self.fs_temp_month_2 * leaves_per_month) +  (self.leave_pending + fs_temp_day2 )
			# 	print('------------available_days------------', self.available_days)
			#       print (self.available_days)
			self.fs_gross_available_days = self.fs_gross_per_day * self.available_days
			print('------------tot salary------------', self.fs_gross_available_days)

	def set_to_draft(self):
		self.write({'state': 'draft'})

	def action_validate(self):
		for obj in self:
			if not obj.account_new_line:
				raise UserError(_('there is no lines in adjustment'))
			final_settlement = obj.final_settlement
			account_move_obj = self.env['account.move']
			journal_id = obj.settlement_type_id.journal_id and obj.settlement_type_id.journal_id.id
			# home_address = obj.employee_id.address_home_id and obj.employee_id.address_home_id.id
			date = obj.resign_date
			total_credit = 0
			total_debit = 0
			narration = 'Final Settlement' + '/'+ str(obj.employee_id.name)
			# period_pool = self.pool.get('account.period')
			# search_periods = period_pool.find(cr, uid, date, context=context)
			# period_id = search_periods[0]
			data_lines = []

			recievable_acc_id = obj.employee_id.bank_account_id and obj.employee_id.bank_account_id.id
			payable_acc_id = obj.employee_id.bank_account_id and obj.employee_id.bank_account_id.id
			if not payable_acc_id or not recievable_acc_id:
				raise UserError(_('set bank account for employee'))
			# if not recievable_acc_id:
			# 	raise UserError(_('set recievable acc in employee home address'))

			for lines in obj.account_new_line:
				total_debit = total_debit + round(lines.debit,2)
				total_credit = total_credit + round(lines.credit,2)

			if total_debit != total_credit:

				raise UserError(_('total debit and credit are not matching'))


			for line in obj.account_new_line:

				vals2 = {
						'journal_id':journal_id,
						'date':date,
						# 'naration':narration,
						'name':narration,
						'account_id':line.account_id.id,
						'debit':line.debit,
						'credit':0.0,
						# 'partner_id':home_address,
				}
				if vals2['debit'] >0.0 or vals2['credit'] >0.0:
					data_lines.append((0,0,vals2),)


				vals1 = {
						'journal_id':journal_id,
						'date':date,
						# 'naration':narration,
						'name':narration,
						'account_id':line.account_id.id,
						'debit':0.0,
						'credit':line.credit,
						# 'partner_id':home_address,
				}
				if vals1['debit'] >0.0 or vals1['credit'] >0.0:
					data_lines.append((0,0,vals1),)


			if data_lines:
				data = {
					'journal_id':journal_id,
					'date':date,
					'state':'draft',
					'company_id':self.employee_id.company_id.id,
					'ref':narration,
					'line_ids':data_lines
				}
				account_move = account_move_obj.create(data)

				self.write({'state':'done','account_move_id':account_move.id})
			else:
				raise UserError(_('no lines for generating journal entry'))

		return True
	#
	def check_accounts_entry(self):
		for obj in self:
			final_settlement = obj.settlement_type_id.final_settlement
			extra_row = {}
			transaction_ids = []
			# recievable_acc_id = obj.employee_id.address_id.property_account_receivable_id and obj.employee_id.address_id.property_account_receivable_id.id
			# payable_acc_id = obj.employee_id.address_id.property_account_payable_id and obj.employee_id.address_id.property_account_payable_id.id
			recievable_acc_id = obj.settlement_type_id.journal_id.default_account_id and obj.settlement_type_id.journal_id.default_account_id.id
			payable_acc_id = obj.settlement_type_id.journal_id.default_account_id and obj.settlement_type_id.journal_id.default_account_id.id
			debit = 0
			credit = 0
			total_due = 0
			total_amt = 0
			total_debit =0
			total_credit =0
			sum_of_negative_values = 0
			sum_of_postive_values = 0
			existing_ids = self.env['final.settlement.new.account.line'].search([('account_line_id','=',obj.id)])
			print('eeeeeeeee', existing_ids)
			if existing_ids:
				existing_ids.unlink()

			for linee in obj.account_line:
				transaction_ids.append(linee.id)
			if not transaction_ids:
				raise UserError(_('generate the transactions first'))
			for line in obj.account_line:
	#            if not obj.account_line:
	#                raise osv.except_osv(_('Warning!'), _('generate the transactions first'))

				total_due = total_due + line.balance
				total_amt = total_amt + line.amount
				if line.balance < 0:
					if line.amount <0:
						sum_of_negative_values = sum_of_negative_values + line.balance
						raise UserError(_('check the signs of balance and amount'))

				if line.balance > 0:
					if line.amount >0:
						sum_of_postive_values = sum_of_postive_values + line.balance
						raise UserError(_('check the signs of balance and amount'))
					credit = line.amount
					debit = 0
				if line.balance < 0:
					if line.amount >= 0:
						credit = 0
						debit = line.amount
					print("::::::::::::sum_of_postive_values",sum_of_postive_values)
					print("::::::::::::sum_of_negative_values",sum_of_negative_values)
					vals = {'account_id':payable_acc_id or False,'account_line_id': obj.id or False,'final_settlement':final_settlement,'debit':math.fabs(debit),'credit':math.fabs(credit),'due':math.fabs(line.balance)}
					self.env['final.settlement.new.account.line'].create(vals)
				else:
					credit = line.amount
					debit = 0
					vals = {'account_id': payable_acc_id or False,
							'account_line_id': obj.id or False,
							'final_settlement': final_settlement, 'debit': math.fabs(debit),
							'credit': math.fabs(credit), 'due': math.fabs(line.balance)}
					self.env['final.settlement.new.account.line'].create(vals)
			if total_due < 0:
				total_debit = 0
				total_credit =total_amt

				extra_row = {'account_id':recievable_acc_id or False,'account_line_id':obj.id or False,'final_settlement':final_settlement,'debit':math.fabs(total_debit),'credit':math.fabs(total_credit)}
			else:
				total_debit = total_amt
				total_credit =0
				extra_row = {'account_id':recievable_acc_id or False,'account_line_id':obj.id or False,'final_settlement':final_settlement,'debit':math.fabs(total_debit),'credit':math.fabs(total_credit)}
			self.env['final.settlement.new.account.line'].create(extra_row)


			# 	if line.balance > 0:
			# 		if line.amount >0:
			# 			sum_of_postive_values = sum_of_postive_values + line.balance
			# 			raise UserError(_('check the signs of balance and amount'))
			#
			# 		credit = line.amount
			#
			# 		debit = 0
			# 	else:
			# 		credit = 0
			# 		debit = line.amount
			# 	print("::::::::::::sum_of_postive_values",sum_of_postive_values)
			# 	print("::::::::::::sum_of_negative_values",sum_of_negative_values)
			# 	vals = {'account_id':line.account_id.id or False,'account_line_id':line.account_line_id.id or False,'final_settlement':final_settlement,'debit':math.fabs(debit),'credit':math.fabs(credit),'due':math.fabs(line.balance)}
			# 	self.env['final.settlement.new.account.line'].create(vals)
			# if total_due < 0:
			# 	total_debit = 0
			# 	total_credit =total_amt
			#
			# 	extra_row = {'account_id':payable_acc_id or False,'account_line_id':obj.id or False,'final_settlement':final_settlement,'debit':math.fabs(total_debit),'credit':math.fabs(total_credit)}
			# else:
			# 	total_debit = total_amt
			# 	total_credit =0
			# 	extra_row = {'account_id':recievable_acc_id or False,'account_line_id':obj.id or False,'final_settlement':final_settlement,'debit':math.fabs(total_debit),'credit':math.fabs(total_credit)}
			# self.env['final.settlement.new.account.line'].create(extra_row)
			self.write({'state':'progress'})
		return True

	#
	def generate_gratuity_value(self):
		experience = 0
		gratuity = 0
		for obj in self:
			# if not obj.contract_type_id:
			# 	raise UserError(_("Please configure contract type in your contract master."))
			obj.gratuity_line_id.unlink()
			terminated = obj.settlement_type_id.termination
			resign = obj.settlement_type_id.final_settlement
			join_date = obj.join_date
			resign_date = obj.resign_date
			# raise UserError(_(obj.join_date))
			if not obj.join_date:
				raise UserError(_("pls provide join date"))
			joining_date = datetime.strptime(str(join_date), "%Y-%m-%d").date()
			gratuity_date = datetime.strptime(str(resign_date), "%Y-%m-%d").date()
			experience = round(float((gratuity_date - joining_date).days)/365.00)
			experiance_days = float((gratuity_date - joining_date).days)
			working_days = ((gratuity_date - joining_date).days + 1)
			contract_ids = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id),('state','=','open')])
			if not contract_ids:
				raise UserError(_('no active contract for this employee'))
			contract_ids = contract_ids[0]
			contract_obj = self.env['hr.contract'].browse(contract_ids).id
			# contract_type = contract_obj.contract_type
			one_month_wage = float(contract_obj.wage * contract_obj.basic_percentage)
			print("---", one_month_wage, "--one_month_wage--")
			max_gratuity = float(contract_obj.wage * contract_obj.basic_percentage * 24)
#                 one_day_wage = float((contract_obj.wage) / 30)

			data_lines = []
			if experience >= 5:
				total_years = experience
				total_years_in_days = total_years * 365
				# gratuity = ((21 * one_day_wage)*5) + (((one_day_wage *30) /365) * extra_year_in_days)
				gratuity = (((one_month_wage * 15)/26) * total_years)
				print("---", gratuity, "--gratuity--")
				vals4 = {
						  'slab':'Over 5 Years',
						  'date_from':joining_date,
						  'date_to':gratuity_date,
						  'no_of_days':working_days,
						  'termination_amount':0,
						  'resign_amount':gratuity,
				}
				data_lines.append((0,0,vals4),)
			self.gratuity_line_id = data_lines
			self.is_gratuity_calculated = True

		return True

	company_id = fields.Many2one('res.company',string="Company", default=lambda self: self.env.user.company_id.id)
	employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
	join_date = fields.Date('Join Date',store=True)
	resign_date = fields.Date(string="Last Working Day")
	settlement_type_id = fields.Many2one('final.settlement.type.master',string="Settlement Type",required=True)
	basic = fields.Float(string="Basic")
	#fs_allowance = fields.Float('Allowance', states={'draft': [('readonly', False)]}, readonly=True)
	# fs_gross_per_day = fields.Float('Per Day Annual leave Salary', states={'draft': [('readonly', False)]},
	# 								readonly=True)
	#hr_allowance_line_ids = fields.One2many('hr.allowance.line','nn_sett_id',string="HR Allowance")
	total_salary = fields.Float('Total Salary')
	payroll_overtime = fields.Float('Overtime')
	payroll_ded = fields.Float('Deductions')
	payroll_add = fields.Float('Additions')
	payroll_allw = fields.Float('Allowances')

	total_net_salary = fields.Float('Net Salary')
	final_settlement_amount = fields.Float('Gratuity Amount')
	final_payment = fields.Float('Final payment')
	department_id = fields.Many2one('hr.department',string="Department",readonly=True)
	job_id =fields.Many2one('hr.job',string='Job', readonly=True)
	# contract_type_id = fields.Char(string='Contract Type')
	fs_temp_year = fields.Float('temp year', states={'draft': [('readonly', False)]}, readonly=True)
	fs_temp_day = fields.Integer('temp day', states={'draft': [('readonly', False)]}, readonly=True)
	fs_total_period = fields.Char('Job Duration', states={'draft': [('readonly', False)]}, readonly=True)
	fs_temp_month_2 = fields.Float('temp month', states={'draft': [('readonly', False)]}, readonly=True)
	# available_days = fields.Float('Balance Leaves', store=True)
	# fs_gross_available_days = fields.Float('Eligible Leave Salary', states={'draft': [('readonly', False)]},
	# 									   readonly=True)
	other_earnings = fields.Float(string="Other Earnings")
	other_deductions = fields.Float(string="Other Deductions")
	reason = fields.Text(string="Reason")
	state = fields.Selection([
			('draft', 'New'),
			('submit', 'Waiting for Approval'),
			('approve', 'Approved'),
			('progress', 'Progress'),
			('done', 'Done'),
			],
			'Status', readonly=True, default='draft', track_visibility='onchange')
	final_settlement = fields.Boolean("Final Settlement")
	# address_home_id = fields.Many2one('res.partner', string='Home Address',readonly=True)
	account_line = fields.One2many('final.settlement.account.line','account_line_id',string="Account Line")
	account_new_line = fields.One2many('final.settlement.new.account.line','account_line_id',string="Account New Line")
	account_move_id = fields.Many2one('account.move', 'Entry', readonly=True)
	gratuity_line_id = fields.One2many('gratuity.employee', 'settlement_grat_id', string="Gratuity Line")
	#leave_pending = fields.Integer(string="Remaining Annual Leaves")
	#leave_pending_balance = fields.Float(string='Leave Balance Amount')
	#last_vacation = fields.Datetime('Last Vacation End Date', states={'draft': [('readonly', False)]}, readonly=True)
	#unpaid_leaves = fields.Integer(string="Unpaid Leaves")
	total_working_days = fields.Float(string="Total Working Days")
	exit_form_count = fields.Integer(compute='compute_exit_form_count')
	no_due_count = fields.Integer(compute='compute_no_due_count')
	is_generated = fields.Boolean(string='Is Generated')
	is_gratuity_calculated = fields.Boolean(string='Is Gratuity Calculated')
	is_final_dues_generated = fields.Boolean(string="Is Final Dues Generated")

	@api.constrains('resign_date')
	def check_expr_date(self):
		for rec in self:
			if rec.resign_date:
				resignation = self.env['hr.resignation'].search(
					[('employee_id', '=', rec.employee_id.id),('state', '=', 'done')], limit=1, order="id desc")
				if not resignation:
					raise ValidationError(
						"Please create the resignation form for this employee and ensure that the resignation is in the Confirmed state")
				if resignation:
					if resignation.actual_date:
						if rec.resign_date < resignation.actual_date:
							raise ValidationError(
								"This employee's last working date is %s, so you cannot select a last working date before this date" % (
									resignation.actual_date))

				# for record in rec.employee_id.contract_ids:
				# 	if record.state == 'open':
				# 		contract_end_date = record.date_end
				# if rec.resign_date < contract_end_date:
				# 	raise ValidationError("Your contract end date is %s, so you cannot resign before this date." % (contract_end_date))

	def compute_exit_form_count(self):
		for rec in self:
			count = self.env['exit.interview'].search_count([('settlement_id', '=', self.id)])
			rec.exit_form_count = count

	def compute_no_due_count(self):
		for rec in self:
			count = self.env['no.due'].search_count([('settlement_id', '=', self.id)])
			rec.no_due_count = count

	def view_exit_interview(self):
		exit_form = self.env['exit.interview'].search([('settlement_id', '=', self.id)], limit=1)
		return {
			'name': _('Exit Interview'),
			'type': 'ir.actions.act_window',
			'res_model': 'exit.interview',
			'res_id': exit_form.id,
			'view_mode': 'form',
			'view_id': False,
			'context': {'create': False},
		}

	def view_no_due(self):
		due_form = self.env['no.due'].search([('settlement_id', '=', self.id)], limit=1)
		return {
			'name': _('No Due'),
			'type': 'ir.actions.act_window',
			'res_model': 'no.due',
			'res_id': due_form.id,
			'view_mode': 'form',
			'view_id': False,
			'context': {'create': False},
		}


	@api.onchange('employee_id')
	def _change_employee(self):
		for rec in self:
			rec.join_date = fields.Datetime.to_string(rec.employee_id.date_join)
			rec.department_id = rec.employee_id.department_id
			rec.job_id = rec.employee_id.job_id
			# leaves_type = self.env['hr.leave.type'].search([('allow_encashment', '=', True)])
			# leaves_allocation = self.env['hr.leave.allocation'].search([('employee_id', '=', rec.employee_id.id),
			# 															('holiday_status_id', 'in', leaves_type.ids),
			# 															('state', '=', 'validate', )])
			# leaves = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id),
			# 													('holiday_status_id', 'in', leaves_type.ids),
			# 															('state', '=', 'validate', )])
			# leaves_allocated = 0
			# leaves_taken = 0
			# balance_leaves = 0
			# for allocation in leaves_allocation:
			# 	leaves_allocated += allocation.number_of_days_display
			# for leave in leaves:
			# 	leaves_taken += leave.number_of_days
			#
			# balance_leaves = leaves_allocated - leaves_taken
			# rec.available_days = balance_leaves
			# print('sssssssssssssssssssssssssssss', leaves, leaves_allocation, balance_leaves)

# class HRallowanceLine(models.Model):
#     _inherit = 'hr.allowance.line'

#     nn_sett_id = fields.Many2one('final.settlement',string="Settlement")

class FinalSettlementAccountLine(models.Model):
	_name = "final.settlement.account.line"
	_description = "final.settlement.account.line"

	account_line_id = fields.Many2one('final.settlement',"settlement")
	account_id = fields.Many2one('account.account',"Account",required=True)
	balance = fields.Float("Balance",readonly=True)
	amount = fields.Float("Payable")
	final_settlement_flag = fields.Boolean("Final Settlement")


class od_final_settlement_new_account_line(models.Model):
	_name = "final.settlement.new.account.line"
	_description = "final.settlement.new.account.line"

	# def create(self, cr, uid, vals, context=None):
	#     if vals.get('account_line_id') or  vals.get('account_id'):
	#         obj = self.pool.get('od.final.settlement').browse(cr,uid,[vals.get('account_line_id')],context)
	#         final_settlement = obj.final_settlement


	#         if final_settlement:
	#             vals['final_settlement'] = final_settlement
	#     return super(od_final_settlement_new_account_line, self).create(cr, uid, vals, context=context)

	account_line_id = fields.Many2one('final.settlement',string="Settlement")
	account_id = fields.Many2one('account.account',string="Account",required=True)
	debit = fields.Float("Debit")
	credit = fields.Float("Credit")
	due = fields.Float("Due")
	final_settlement = fields.Boolean("Final Settlement")


class FinalSettlementTypeMaster(models.Model):
	_name = "final.settlement.type.master"

	name = fields.Char("Name" ,required=True)
	final_settlement = fields.Boolean("Resign")
	remarks = fields.Text("Remarks")
	termination = fields.Boolean("Termination")
	journal_id = fields.Many2one('account.journal',string="Journal",required=True)
	settlement_type_master_line = fields.One2many('final.settlement.type.master.line','settlement_type_master_line_id',string="Settlement Line")

	@api.onchange('journal_id')
	def onchange_journal(self):
		for rec in self:
			lines = [(5, 0, 0)]
			if self.journal_id.default_account_id:
				vals = {
					'account_id': self.journal_id.default_account_id.id
				}
				lines.append((0, 0, vals))
				rec.settlement_type_master_line = lines
			if self.journal_id.default_account_id:
				vals = {
					'account_id': self.journal_id.default_account_id.id
				}
				lines.append((0, 0, vals))
				rec.settlement_type_master_line = lines

class FinalSettlementTypeMasterLine(models.Model):
	_name = "final.settlement.type.master.line"

	account_id = fields.Many2one('account.account',"Account")
	settlement_type_master_line_id = fields.Many2one('final.settlement.type.master')


class GratuityCalculation(models.Model):
	_name = "gratuity.employee"

	slab = fields.Char(string="Slab")
	date_from = fields.Date(string="Date From")
	date_to = fields.Date(string="Date To")
	no_of_days = fields.Float(string="Num of Days Working")
	termination_amount = fields.Float(string="Termination")
	resign_amount = fields.Float(string="Resignation")
	settlement_grat_id = fields.Many2one('final.settlement', string="Settlement")


# class Contract(models.Model):
# 	_inherit = 'hr.contract'
#
# 	contract_type = fields.Selection([('limited', 'Limited'), ('unlimited', 'Unlimited')],
# 									string="Contract Type", default="limited")

#
# class HrEmployees(models.Model):
#     _inherit = 'hr.employee.base'
#
#     join_date = fields.Date('Date of Join')