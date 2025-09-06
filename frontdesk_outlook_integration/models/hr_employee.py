# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    outlook_access_token = fields.Text(string='Outlook Access Token', groups='base.group_system')
    outlook_refresh_token = fields.Text(string='Outlook Refresh Token', groups='base.group_system')
    outlook_token_expiry = fields.Datetime(string='Token Expiry', groups='base.group_system')
    outlook_calendar_sync = fields.Boolean(string='Enable Outlook Calendar Sync', default=False)
    outlook_calendar_id = fields.Char(string='Outlook Calendar ID', groups='base.group_system')
    
    def action_setup_outlook_sync(self):
        """Open wizard to setup Outlook calendar sync for employee"""
        return {
            'name': _('Setup Outlook Calendar Sync'),
            'type': 'ir.actions.act_window',
            'res_model': 'outlook.setup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': self.id,
            }
        }