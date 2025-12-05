# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    outlook_access_token = fields.Text(string='Outlook Access Token', groups='base.group_system')
    outlook_refresh_token = fields.Text(string='Outlook Refresh Token', groups='base.group_system')
    outlook_token_expiry = fields.Datetime(string='Token Expiry', groups='base.group_system')
    outlook_calendar_sync = fields.Boolean(string='Enable Outlook Calendar Sync', default=False)
    outlook_calendar_id = fields.Char(string='Outlook Calendar ID', groups='base.group_system')
    
    def action_setup_outlook_sync(self):
        """Setup Outlook calendar sync for employee"""
        outlook_config = self.env['outlook.config'].search([('active', '=', True)], limit=1)
        if not outlook_config:
            raise UserError(_('No active Outlook configuration found. Please configure Outlook settings first.'))
        
        auth_url = outlook_config.get_auth_url(employee_id=self.id)
        return {
            'type': 'ir.actions.act_url',
            'url': auth_url,
            'target': 'new',
        }