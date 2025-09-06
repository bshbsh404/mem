import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SmsSms(models.Model):
    _inherit = 'sms.sms'

    def _validate_sms_number(self, number):
        """Check if the number belongs to a partner, visitor, or employee."""
        # Check in res.partner
        models_to_check = [
            ('res.partner', 'phone', 'Partner'),
            ('frontdesk.visitor', 'phone', 'Visitor'),
            ('hr.employee', 'work_phone', 'Employee')
        ]
        try:
            for model, field, entity in models_to_check:
                record = self.env[model].sudo().search_read([(field, '=', number)], ['id'], limit=1)
                record = record[0] if record else None
                if record:
                    _logger.info("Phone number %s belongs to %s: %s", number, entity, record['id'])
                    return True
        except Exception as e:
            _logger.error("Error validating phone number %s: %s", number, str(e))
            return False

        # Number is not associated with any known entity
        _logger.warning("Phone number %s does not belong to any Partner, Visitor, or Employee.", number)
        return False
    
    def _send(self, unlink_failed=False, unlink_sent=True, raise_exception=False, using_template=False):
        """Send SMS using a custom API after checking the number (presence and formatting)."""
        # Loop through each SMS record to send
        if not using_template:
            raise UserError(_("You are not allowed to send an SMS."))

        for sms in self:
            try:

                # Validate if the number belongs to a partner, visitor, or employee
                is_valid = self._validate_sms_number(sms.number)
                if not is_valid:
                    raise UserError(_("The phone number %s does not belong to any visitor or employee.") % sms.number)
                
                # Fetch the SMS API configuration from system parameters
                api_url = self.env['ir.config_parameter'].sudo().get_param('sms.nama_api_url')
                bank_code = self.env['ir.config_parameter'].sudo().get_param('sms.nama_bank_code')
                bank_pwd = self.env['ir.config_parameter'].sudo().get_param('sms.nama_bank_pwd')
                sender_id = self.env['ir.config_parameter'].sudo().get_param('sms.nama_sender_id')

                if not all([api_url, bank_code, bank_pwd, sender_id]):
                    raise UserError(_("SMS API configuration is incomplete. Please check the system parameters."))

                # Prepare the request payload
                payload = {
                    "BankCode": bank_code,
                    "BankPWD": bank_pwd,
                    "SenderID": sender_id,
                    "MsgText": sms.body,
                    "MobileNo": sms.number.replace(" ", "").replace("+", "")
                }
                headers = {"Content-Type": "application/json"}

                # Send the POST request to the SMS API
                response = requests.post(api_url, json=payload, headers=headers)

                # Check the response from the SMS API
                if response.status_code == 200:
                    sms.write({'state': 'sent', 'failure_type': False})
                    _logger.info(f"SMS successfully sent to {sms.number}")
                else:
                    _logger.error(response)
                    error_message = response.json().get('message', 'Unknown error')
                    sms.write({'state': 'error', 'failure_type': 'sms_server'})
                    _logger.error(f"Failed to send SMS to {sms.number}. Error: {error_message}")

            except Exception as e:
                sms.write({'state': 'error', 'failure_type': 'sms_server'})
                _logger.error(f"Error sending SMS to {sms.number}: {str(e)}")
                if raise_exception:
                    raise UserError(_("Failed to send SMS due to: %s") % str(e))

        # Notify related mail messages about the SMS status update
        self.mapped('mail_message_id')._notify_message_notification_update()
