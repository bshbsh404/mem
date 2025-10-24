# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class FrontdeskVisitor(models.Model):
    _inherit = 'frontdesk.visitor'

    # Add field to track if notification was sent
    push_notification_sent = fields.Boolean(
        string='Push Notification Sent',
        default=False,
        help='Indicates whether push notification was sent for this visit'
    )
    
    @api.model
    def create(self, vals_list):
        """Override create to send push notifications for new visits"""
        visitors = super(FrontdeskVisitor, self).create(vals_list)
        
        # Send push notifications for new visits
        for visitor in visitors:
            _logger.error(f"_send_push_notification_if_enabled for visitor ID: {visitor.id}")
            visitor._send_push_notification_if_enabled()
        
        return visitors
    
    def _send_push_notification_if_enabled(self):
        """Send push notification if enabled and conditions are met"""
        self.ensure_one()
        
        # Check if push notifications are enabled
        config_settings = self.env['res.config.settings']
        push_config = config_settings.get_push_config()
        _logger.error(f"_send_push_notification_if_enabled Push notification config: {push_config}")
        
        if not push_config.get('enabled'):
            _logger.error("Push notifications are disabled")
            return
        
        # Check if employee exists and has necessary information
        if not self.employee_id:
            _logger.error(f"No employee assigned to visitor {self.id}, skipping push notification")
            return
        
        # Get employee's USER_ID (we'll use employee ID as USER_ID for now)
        # In a real implementation, you might have a specific field mapping employee to USER_ID
        user_id = self._get_employee_user_id()
        if not user_id:
            _logger.error(f"No USER_ID found for employee {self.employee_id.name}, skipping push notification")
            return
        
        # Prepare notification content
        title = "New Visit Request"
        message = f"You have a new visit request from {self.partner_id.name}"
        
        # Send the notification
        result = self._send_push_notification_api(user_id, title, message, push_config)
        
        # Update the flag based on result
        if result.get('success'):
            self.push_notification_sent = True
            _logger.error(f"Push notification sent successfully for visitor {self.id}")
        else:
            _logger.error(f"Failed to send push notification for visitor {self.id}: {result.get('error')}")
    
    def _get_employee_user_id(self):
        """Get the USER_ID for push notifications from employee"""
        self.ensure_one()
        
        if not self.employee_id:
            return None
        
        # Try to get USER_ID from employee
        # First check if employee has a specific push_user_id field
        if hasattr(self.employee_id, 'push_user_id') and self.employee_id.push_user_id:
            return self.employee_id.push_user_id
        
        # Fallback to employee ID
        return self.employee_id.id
    
    def _send_push_notification_api(self, user_id, title, message, push_config):
        """Send push notification via API"""
        try:
            import requests
            import json
            
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
            auth = None
            if push_config.get('username') and push_config.get('password'):
                auth = (push_config['username'], push_config['password'])
            
            # Make the API request
            response = requests.post(
                push_config['api_url'],
                json=payload,
                auth=auth,
                timeout=push_config.get('timeout', 30),
                headers={'Content-Type': 'application/json'}
            )
            
            # Log the request and response
            _logger.error(f"Push notification request payload: {json.dumps(payload)}")
            _logger.error(f"Push notification response status: {response.status_code}, Response: {response.text}")
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'response': response.json() if response.content else {},
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def resend_push_notification(self):
        """Manual action to resend push notification"""
        self.ensure_one()
        
        # Reset the flag and send notification
        self.push_notification_sent = False
        self._send_push_notification_if_enabled()
        
        if self.push_notification_sent:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Push notification sent successfully',
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Failed',
                    'message': 'Failed to send push notification. Check logs for details.',
                    'type': 'danger',
                }
            }