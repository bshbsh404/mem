# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
import logging
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from werkzeug import urls

_logger = logging.getLogger(__name__)


class OutlookConfig(models.Model):
    _name = 'outlook.config'
    _description = 'Microsoft Outlook Configuration'

    name = fields.Char(string='Configuration Name', required=True, default='Default Outlook Config')
    client_id = fields.Char(string='Client ID', required=True, help="Microsoft Application (client) ID")
    client_secret = fields.Char(string='Client Secret', required=True, help="Microsoft Client secret value")
    tenant_id = fields.Char(string='Tenant ID', required=True, help="Microsoft Directory (tenant) ID")
    redirect_uri = fields.Char(string='Redirect URI', default='http://localhost:8000/auth', help="Redirect URI configured in Azure")
    active = fields.Boolean(string='Active', default=True)

    def get_auth_url(self):
        """Generate authorization URL for Microsoft OAuth"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'https://graph.microsoft.com/Calendars.ReadWrite offline_access',
            'response_mode': 'query',
        }
        
        auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize?{urls.url_encode(params)}"
        return auth_url

    def get_access_token(self, auth_code):
        """Exchange authorization code for access token"""
        try:
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': auth_code,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code',
                'scope': 'https://graph.microsoft.com/Calendars.ReadWrite offline_access',
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'access_token' in result:
                return {
                    'access_token': result.get('access_token'),
                    'refresh_token': result.get('refresh_token'),
                    'expires_in': result.get('expires_in', 3600)
                }
            return None
        except Exception as e:
            _logger.error(f"Error getting access token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token):
        """Refresh access token using refresh token"""
        try:
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
                'scope': 'https://graph.microsoft.com/Calendars.ReadWrite offline_access',
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'access_token' in result:
                return {
                    'access_token': result.get('access_token'),
                    'refresh_token': result.get('refresh_token', refresh_token),
                    'expires_in': result.get('expires_in', 3600)
                }
            return None
        except Exception as e:
            _logger.error(f"Error refreshing access token: {e}")
            return None