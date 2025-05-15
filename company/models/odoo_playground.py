from email.policy import default
from odoo.tools.safe_eval import safe_eval
from odoo import api, models, fields,tools
class OdooPlayground(models.Model):
    _name = "odoo.playground"
    _description = 'Odoo  Playground'


    DEFAULT_ENV_VARIABLE=("""#  Available variables 
          # -self.user.is_authenticated
          # 
          # self.session.is_active
          # 
          # self.config.debug_mode
          # 
          # self.db.connection_status
          # 
          # self.user.has_permission('admin')
          # 
          # self.settings.is_enabled
          # 
          # self.device.is_online
          # 
          # self.order.status
          # 
          # self.profile.is_complete
          # 
          # self.server.is_running
          # 
          # self.task.is_completed
          # 
          # self.data.is_valid
          # 
          # self.user.role
          # 
          # self.network.is_connected
          # 
          # self.order.total_price
          # 
          # self.customer.is_verified
          # 
          # self.window.is_maximized
          # 
          # self.api.is_connected
          # 
          # self.theme.is_dark_mode
          # 
          # self.cart.is_empty
          # 
          # self.notification.is_read
          # 
          # self.app.is_running
          # 
          # self.cache.is_enabled
           \n\n\n\n """)


    model_id = fields.Many2one('ir.model',string='Model')
    code =fields.Text(string='Code',default=DEFAULT_ENV_VARIABLE)
    result = fields.Text(string='Result')

    def action_execute(self):
        try:
            if self.model_id:
                # Ensure you are using the correct model reference in the environment
                model = self.env[self.model_id.model]
            else:
                # If no model_id, then you are evaluating the code
                self.result = safe_eval(self.code.strip(), {'self': self})
                return  # No further action required if evaluating code only

            # If model exists, you might want to do something with it here
            self.result = 'Model is successfully loaded.'

        except Exception as e:
            # Catching any exception and setting the result to the error message
            self.result = str(e)
