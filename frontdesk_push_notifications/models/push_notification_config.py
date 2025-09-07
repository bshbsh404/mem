# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
import requests
import logging
import json

_logger = logging.getLogger(__name__)


class PushNotificationConfig(models.Model):
    _name = 'push.notification.config'
    _description = 'Push Notification Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Configuration Name', required=True, default='Default Push Config')
    api_url = fields.Char(
        string='API URL', 
        required=True,
        default='https://owwscccsp.nws.nama.om/api/custom/nwscustompushnotification/fusiontrigger',
        help='Push notification API endpoint'
    )
    username = fields.Char(string='Username', required=True, help='Basic auth username')
    password = fields.Char(string='Password', required=True, help='Basic auth password')
    active = fields.Boolean(string='Active', default=True)
    timeout = fields.Integer(string='Request Timeout (seconds)', default=30)
    
    # Test connection functionality
    test_user_id = fields.Integer(string='Test User ID', help='User ID for testing notifications')
    
    @api.model
    def get_active_config(self):
        """Get the active push notification configuration"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            _logger.warning("No active push notification configuration found")
        return config
    
    def send_push_notification(self, user_id, title, message):
        """Send a push notification using the configured API"""
        self.ensure_one()
        
        if not self.active:
            _logger.info("Push notification config is not active, skipping notification")
            return {'success': False, 'error': 'Configuration not active'}
        
        try:
            # Prepare the request payload
            payload = {
                "data": [
                    {
                        "USER_ID": user_id,
                        "TITTLE": title,  # Note: API uses "TITTLE" (with double T)
                        "MESSAGE": message
                    }
                ]
            }
            
            # Prepare authentication
            auth = (self.username, self.password) if self.username and self.password else None
            
            # Make the API request
            response = requests.post(
                self.api_url,
                json=payload,
                auth=auth,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            # Log the request and response
            _logger.info(f"Push notification sent to user {user_id}: {title}")
            _logger.debug(f"Request payload: {json.dumps(payload)}")
            _logger.debug(f"Response status: {response.status_code}, Response: {response.text}")
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'response': response.json() if response.content else {},
                    'status_code': response.status_code
                }
            else:
                _logger.error(f"Push notification failed with status {response.status_code}: {response.text}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"Push notification timeout after {self.timeout} seconds"
            _logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Push notification request failed: {str(e)}"
            _logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error sending push notification: {str(e)}"
            _logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def test_connection(self):
        """Test the push notification API connection"""
        self.ensure_one()
        
        if not self.test_user_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Test Failed',
                    'message': 'Please set a Test User ID first',
                    'type': 'warning',
                }
            }
        
        result = self.send_push_notification(
            user_id=self.test_user_id,
            title='Test Notification',
            message='This is a test notification from Odoo Frontdesk module'
        )
        
        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Test Successful',
                    'message': 'Push notification sent successfully',
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Test Failed',
                    'message': f"Error: {result.get('error', 'Unknown error')}",
                    'type': 'danger',
                }
            }