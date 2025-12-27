# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class FrontdeskCosecLog(models.Model):
    _name = 'frontdesk.cosec.log'
    _description = 'COSEC API Log'
    _order = 'create_date desc'

    visitor_id = fields.Many2one('frontdesk.visitor', string='Visitor', required=True)
    emp_id = fields.Char(string='Employee ID')
    qr_string = fields.Char(string='QR Code')
    
    # API Details
    api_url = fields.Char(string='API URL')
    request_data = fields.Text(string='Request Data')
    response_data = fields.Text(string='Response Data')
    response_status = fields.Char(string='Response Status')
    
    # Status
    state = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('error', 'Error')
    ], string='Status', default='pending')
    
    # Error Details
    error_message = fields.Text(string='Error Message')
    
    # Timestamps
    create_date = fields.Datetime(string='Created', default=fields.Datetime.now)
    sent_date = fields.Datetime(string='Sent Date')
    
    def action_retry(self):
        """Retry sending data to COSEC"""
        self.ensure_one()
        try:
            # Get COSEC config
            config = self.env['frontdesk.cosec.config'].get_active_config()
            
            # Send data again
            success = self._send_to_cosec(config)
            
            if success:
                self.write({
                    'state': 'success',
                    'sent_date': fields.Datetime.now()
                })
            else:
                self.write({'state': 'failed'})
                
        except Exception as e:
            self.write({
                'state': 'error',
                'error_message': str(e)
            })
    
    def action_retry_multiple(self):
        """Retry sending data to COSEC for multiple records"""
        failed_logs = self.filtered(lambda log: log.state in ['failed', 'error'])
        
        if not failed_logs:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Info',
                    'message': 'No failed logs to retry',
                    'type': 'info',
                }
            }
        
        success_count = 0
        error_count = 0
        
        for log in failed_logs:
            try:
                config = self.env['frontdesk.cosec.config'].get_active_config()
                success = log._send_to_cosec(config)
                
                if success:
                    log.write({
                        'state': 'success',
                        'sent_date': fields.Datetime.now()
                    })
                    success_count += 1
                else:
                    log.write({'state': 'failed'})
                    error_count += 1
                    
            except Exception as e:
                log.write({
                    'state': 'error',
                    'error_message': str(e)
                })
                error_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Retry Complete',
                'message': f'Successfully retried {success_count} logs. Failed: {error_count}',
                'type': 'success' if success_count > 0 else 'warning',
            }
        }
    
    def _send_to_cosec(self, config):
        """Send visitor data to COSEC API"""
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            # Prepare data
            emp_id_with_prefix = f"{config.emp_id_prefix}{self.emp_id}" if self.emp_id else "UNKNOWN"
            
            # Build URL with parameters - using the correct format from the example
            url = f"{config.api_url}?action=set;id={emp_id_with_prefix};active=0"
            
            # Make request
            response = requests.get(
                url,
                auth=HTTPBasicAuth(config.username, config.password),
                timeout=30,
                verify=False
            )
            
            # Update log
            self.write({
                'api_url': url,
                'request_data': f"emp_id: {emp_id_with_prefix}, qr_string: {self.qr_string}",
                'response_data': response.text,
                'response_status': str(response.status_code),
                'sent_date': fields.Datetime.now()
            })
            
            # Check for success response
            response_text = response.text.strip()
            if response.status_code == 200:
                # Check if response contains success indicators
                if ('success' in response_text.lower() or 
                    'saved successfully' in response_text.lower() or
                    '0070200001' in response_text):
                    return True
                else:
                    # Log the actual response for debugging
                    _logger.warning(f"COSEC API returned unexpected response: {response_text}")
                    return False
            else:
                return False
                
        except Exception as e:
            self.write({
                'error_message': str(e),
                'sent_date': fields.Datetime.now()
            })
            return False
    
    @api.model
    def auto_retry_failed_logs(self, max_retries=3):
        """Automatically retry failed logs with limited attempts"""
        from datetime import timedelta
        
        failed_logs = self.search([
            ('state', 'in', ['failed', 'error']),
            ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))  # Only retry recent failures
        ])
        
        if not failed_logs:
            return {'message': 'No failed logs to retry'}
        
        success_count = 0
        error_count = 0
        
        for log in failed_logs:
            try:
                config = self.env['frontdesk.cosec.config'].get_active_config()
                success = log._send_to_cosec(config)
                
                if success:
                    log.write({
                        'state': 'success',
                        'sent_date': fields.Datetime.now()
                    })
                    success_count += 1
                else:
                    log.write({'state': 'failed'})
                    error_count += 1
                    
            except Exception as e:
                log.write({
                    'state': 'error',
                    'error_message': str(e)
                })
                error_count += 1
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'message': f'Retried {len(failed_logs)} logs. Success: {success_count}, Failed: {error_count}'
        }
