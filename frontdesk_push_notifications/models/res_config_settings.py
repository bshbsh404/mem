# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Push notification settings
    push_notification_enabled = fields.Boolean(
        string='Enable Push Notifications',
        config_parameter='frontdesk_push_notifications.enabled',
        help='Enable automatic push notifications for new visit requests'
    )
    
    push_api_url = fields.Char(
        string='Push API URL',
        config_parameter='frontdesk_push_notifications.api_url',
        default='https://owwscccsp.nws.nama.om/api/custom/nwscustompushnotification/fusiontrigger'
    )
    
    push_api_username = fields.Char(
        string='API Username',
        config_parameter='frontdesk_push_notifications.username'
    )
    
    push_api_password = fields.Char(
        string='API Password',
        config_parameter='frontdesk_push_notifications.password'
    )
    
    push_api_timeout = fields.Integer(
        string='API Timeout (seconds)',
        config_parameter='frontdesk_push_notifications.timeout',
        default=30
    )
    
    @api.model
    def get_push_config(self):
        """Get current push notification configuration"""
        return {
            'enabled': self.env['ir.config_parameter'].sudo().get_param('frontdesk_push_notifications.enabled', False),
            'api_url': self.env['ir.config_parameter'].sudo().get_param(
                'frontdesk_push_notifications.api_url', 
                'https://owwscccsp.nws.nama.om/api/custom/nwscustompushnotification/fusiontrigger'
            ),
            'username': self.env['ir.config_parameter'].sudo().get_param('frontdesk_push_notifications.username'),
            'password': self.env['ir.config_parameter'].sudo().get_param('frontdesk_push_notifications.password'),
            'timeout': int(self.env['ir.config_parameter'].sudo().get_param('frontdesk_push_notifications.timeout', 30)),
        }