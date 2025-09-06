# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
import logging
import msal
from odoo import models, fields, api, _
from datetime import datetime, timedelta

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
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        scopes = ["https://graph.microsoft.com/Calendars.ReadWrite"]
        
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret,
        )
        
        auth_url = app.get_authorization_request_url(
            scopes,
            redirect_uri=self.redirect_uri
        )
        return auth_url

    def get_access_token(self, auth_code):
        """Exchange authorization code for access token"""
        try:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            scopes = ["https://graph.microsoft.com/Calendars.ReadWrite"]
            
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret,
            )
            
            result = app.acquire_token_by_authorization_code(
                auth_code,
                scopes=scopes,
                redirect_uri=self.redirect_uri
            )
            
            return result.get('access_token') if result else None
        except Exception as e:
            _logger.error(f"Error getting access token: {e}")
            return None