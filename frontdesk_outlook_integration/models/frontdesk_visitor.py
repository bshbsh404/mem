# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
import json
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class FrontdeskVisitor(models.Model):
    _inherit = 'frontdesk.visitor'
    
    outlook_event_id = fields.Char(string='Outlook Event ID', readonly=True)
    outlook_event_url = fields.Char(string='Outlook Event URL', readonly=True)
    outlook_sync_status = fields.Selection([
        ('not_synced', 'Not Synced'),
        ('synced', 'Synced'),
        ('sync_failed', 'Sync Failed'),
        ('cancelled', 'Cancelled')
    ], string='Outlook Sync Status', default='not_synced', readonly=True)
    
    def create_outlook_event(self):
        """Create event in host employee's Outlook calendar"""
        for visitor in self:
            _logger.info(f'create_outlook_event called for visitor {visitor.id} ({visitor.partner_id.name})')
            if not visitor.employee_id:
                _logger.info(f'Skipping Outlook sync for visitor {visitor.id}: No host employee assigned')
                continue
                
            host = visitor.employee_id
            _logger.info(f'Checking host {host.name} for visitor {visitor.id}')
            if not host.outlook_calendar_sync:
                _logger.info(f'Skipping host {host.name}: Outlook calendar sync not enabled')
                continue
            if not host.outlook_access_token:
                _logger.info(f'Skipping host {host.name}: No Outlook access token')
                continue
                
            try:
                event_data = visitor._prepare_outlook_event_data()
                event_id = visitor._send_outlook_request(host, 'POST', '/events', event_data)
                
                if event_id:
                    visitor.write({
                        'outlook_event_id': event_id,
                        'outlook_sync_status': 'synced'
                    })
                    _logger.info(f'Created Outlook event {event_id} for visitor {visitor.partner_id.name}')
                else:
                    visitor.outlook_sync_status = 'sync_failed'
                    
            except Exception as e:
                _logger.error(f'Error creating Outlook event for visitor {visitor.partner_id.name}: {e}')
                visitor.outlook_sync_status = 'sync_failed'
    
    def update_outlook_event(self):
        """Update existing Outlook event"""
        for visitor in self:
            if not visitor.outlook_event_id:
                continue
                
            if not visitor.employee_id:
                continue
                
            host = visitor.employee_id
            if not host.outlook_calendar_sync or not host.outlook_access_token:
                continue
                
            try:
                event_data = visitor._prepare_outlook_event_data()
                success = visitor._send_outlook_request(
                    host, 'PATCH', f'/events/{visitor.outlook_event_id}', event_data
                )
                
                if success:
                    _logger.info(f'Updated Outlook event {visitor.outlook_event_id} for visitor {visitor.partner_id.name}')
                else:
                    visitor.outlook_sync_status = 'sync_failed'
                    
            except Exception as e:
                _logger.error(f'Error updating Outlook event for visitor {visitor.partner_id.name}: {e}')
                visitor.outlook_sync_status = 'sync_failed'
    
    def cancel_outlook_event(self):
        """Cancel/delete Outlook event"""
        for visitor in self:
            if not visitor.outlook_event_id:
                continue
                
            if not visitor.employee_id:
                continue
                
            host = visitor.employee_id
            if not host.outlook_calendar_sync or not host.outlook_access_token:
                continue
                
            try:
                success = visitor._send_outlook_request(
                    host, 'DELETE', f'/events/{visitor.outlook_event_id}'
                )
                
                if success:
                    visitor.write({
                        'outlook_event_id': False,
                        'outlook_sync_status': 'cancelled'
                    })
                    _logger.info(f'Cancelled Outlook event for visitor {visitor.partner_id.name}')
                else:
                    visitor.outlook_sync_status = 'sync_failed'
                    
            except Exception as e:
                _logger.error(f'Error cancelling Outlook event for visitor {visitor.partner_id.name}: {e}')
                visitor.outlook_sync_status = 'sync_failed'
    
    def _prepare_outlook_event_data(self):
        """Prepare event data for Outlook API"""
        if self.planned_time is not None:
            start_time = datetime.combine(self.planned_date, datetime.min.time()) + timedelta(hours=int(self.planned_time), minutes=(self.planned_time % 1) * 60)
        else:
            start_time = datetime.combine(self.planned_date or self.date, datetime.min.time())
        
        end_time = start_time + timedelta(minutes=self.planned_duration or 60)
        
        return {
            'subject': f'Visit: {self.partner_id.name}',
            'body': {
                'contentType': 'HTML',
                'content': f"""
                    <p><strong>Visitor:</strong> {self.partner_id.name}</p>
                    <p><strong>Phone:</strong> {self.phone or 'N/A'}</p>
                    <p><strong>Email:</strong> {self.email or 'N/A'}</p>
                    <p><strong>Company:</strong> {self.company_id.name if self.company_id else 'N/A'}</p>
                    <p><strong>Purpose:</strong> {self.visit_purpose or 'N/A'}</p>
                    <p><strong>Location:</strong> {self.location_description or 'N/A'}</p>
                """
            },
            'start': {
                'dateTime': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'UTC'
            },
            'attendees': [
                {
                    'emailAddress': {
                        'address': self.email or '',
                        'name': self.partner_id.name
                    }
                }
            ],
            'categories': ['Frontdesk Visit']
        }
    
    def _send_outlook_request(self, host, method, endpoint, data=None):
        """Send request to Microsoft Graph API"""
        access_token = host.outlook_access_token
        
        if host.outlook_token_expiry and host.outlook_token_expiry <= datetime.now():
            access_token = self._refresh_host_token(host)
            if not access_token:
                _logger.error('Failed to refresh access token')
                return False
        
        url = f'https://graph.microsoft.com/v1.0/me{endpoint}'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False
                
            if response.status_code in [200, 201, 204]:
                if method == 'POST':
                    return response.json().get('id')
                return True
            elif response.status_code == 401:
                access_token = self._refresh_host_token(host)
                if access_token:
                    return self._send_outlook_request(host, method, endpoint, data)
                return False
            else:
                _logger.error(f'Outlook API error: {response.status_code} - {response.text}')
                return False
                
        except Exception as e:
            _logger.error(f'Error sending Outlook request: {e}')
            return False
    
    def _refresh_host_token(self, host):
        """Refresh host's Outlook access token"""
        if not host.outlook_refresh_token:
            return None
            
        outlook_config = self.env['outlook.config'].search([('active', '=', True)], limit=1)
        if not outlook_config:
            return None
            
        token_data = outlook_config.refresh_access_token(host.outlook_refresh_token)
        if token_data:
            host.write({
                'outlook_access_token': token_data['access_token'],
                'outlook_refresh_token': token_data.get('refresh_token', host.outlook_refresh_token),
                'outlook_token_expiry': datetime.now() + timedelta(seconds=token_data['expires_in'])
            })
            return token_data['access_token']
        return None
    
    @api.model
    def create(self, vals):
        """Override create to sync with Outlook when visit is created"""
        visitor = super(FrontdeskVisitor, self).create(vals)
        if visitor.state in ['planned', 'checked_in']:
            visitor.create_outlook_event()
        return visitor
    
    def write(self, vals):
        """Override write to sync with Outlook when visit is updated"""
        result = super(FrontdeskVisitor, self).write(vals)
        
        # If visit is approved/accepted, create Outlook event
        if vals.get('state') in ['planned', 'checked_in'] and not self.outlook_event_id:
            self.create_outlook_event()
        
        # If visit details changed, update Outlook event
        elif self.outlook_event_id and any(field in vals for field in ['planned_date', 'planned_time', 'planned_duration', 'visit_purpose']):
            self.update_outlook_event()
        
        # If visit is cancelled, cancel Outlook event
        elif vals.get('state') == 'canceled' and self.outlook_event_id:
            self.cancel_outlook_event()
        
        return result