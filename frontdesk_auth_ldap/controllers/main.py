import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class AzureADWebhook(http.Controller):

    @http.route('/azure_ad/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def azure_ad_webhook(self, **kwargs):
        # Handle Azure AD subscription validation
        validation_token = request.params.get('validationToken')
        if validation_token:
            _logger.info("Azure AD webhook validation request received")
            return validation_token

        # Process incoming notifications
        try:
            payload = request.jsonrequest
            _logger.info("Received Azure AD webhook payload: %s", payload)

            for event in payload.get('value', []):
                user_data = event.get('resourceData', {})
                email = user_data.get('mail')
                name = user_data.get('displayName', 'Unknown')
                phone = user_data.get('telephoneNumber', '')
                department_name = user_data.get('department', '')

                if not email:
                    _logger.warning("Skipping Azure AD user without email")
                    continue

                # Ensure user exists or create one
                user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
                if not user:
                    user = request.env['res.users'].sudo().create({
                        'name': name,
                        'login': email,
                        'email': email,
                        'active': True,
                    })
                    _logger.info("Created new Odoo user: %s", email)

                # Ensure employee exists or create one
                employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
                if not employee:
                    department = request.env['hr.department'].sudo().search([('name', '=', department_name)], limit=1)
                    if not department and department_name:
                        department = request.env['hr.department'].sudo().create({'name': department_name})
                        _logger.info("Created new department: %s", department_name)

                    request.env['hr.employee'].sudo().create({
                        'name': name,
                        'work_email': email,
                        'work_phone': phone,
                        'user_id': user.id,
                        'department_id': department.id if department else None,
                    })
                    _logger.info("Created new Odoo employee for user: %s", email)

            return {"status": "success"}
        except Exception as e:
            _logger.error("Error processing Azure AD webhook: %s", e, exc_info=True)
            return {"status": "error", "message": str(e)}