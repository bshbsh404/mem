# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class FrontdeskVisitor(models.Model):
    _inherit = 'frontdesk.visitor'

    cosec_log_ids = fields.One2many('frontdesk.cosec.log', 'visitor_id', string='COSEC Logs')
    cosec_sent = fields.Boolean(string='Sent to COSEC', default=False)
    cosec_last_sent = fields.Datetime(string='Last Sent to COSEC')

    @api.model
    def create(self, values):
        """Override create to send data to COSEC after visitor creation"""
        visitor = super(FrontdeskVisitor, self).create(values)
        
        # Send to COSEC if integration is enabled
        try:
            visitor._send_to_cosec_system()
        except Exception as e:
            _logger.error(f"Error sending visitor {visitor.id} to COSEC: {str(e)}")
        
        return visitor

    def _send_to_cosec_system(self):
        """Send visitor data to COSEC system"""
        self.ensure_one()
        
        try:
            # Check if COSEC integration is enabled
            config = self.env['frontdesk.cosec.config'].search([('active', '=', True)], limit=1)
            if not config or not config.enable_cosec_integration:
                _logger.info("COSEC integration is disabled")
                return False
            
            # Check if this station should send to COSEC
            if config.station_ids and self.station_id not in config.station_ids:
                _logger.info(f"Station {self.station_id.name} not configured for COSEC")
                return False
            
            # Create log entry
            log_vals = {
                'visitor_id': self.id,
                'emp_id': self.emp_id or '',
                'qr_string': self.qr_string or '',
                'state': 'pending'
            }
            
            log = self.env['frontdesk.cosec.log'].create(log_vals)
            
            # Send data to COSEC
            success = log._send_to_cosec(config)
            
            if success:
                log.write({'state': 'success'})
                self.write({
                    'cosec_sent': True,
                    'cosec_last_sent': fields.Datetime.now()
                })
                _logger.info(f"Successfully sent visitor {self.id} to COSEC")
                return True
            else:
                log.write({'state': 'failed'})
                _logger.error(f"Failed to send visitor {self.id} to COSEC")
                return False
                
        except Exception as e:
            _logger.error(f"Error in _send_to_cosec_system for visitor {self.id}: {str(e)}")
            return False

    def action_send_to_cosec(self):
        """Manual action to send visitor data to COSEC"""
        self.ensure_one()
        try:
            success = self._send_to_cosec_system()
            if success:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'Visitor data sent to COSEC successfully!',
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error',
                        'message': 'Failed to send visitor data to COSEC',
                        'type': 'danger',
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Error: {str(e)}',
                    'type': 'danger',
                }
            }
    
    def action_view_cosec_logs(self):
        """Open COSEC logs for this visitor"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'COSEC Logs',
            'res_model': 'frontdesk.cosec.log',
            'view_mode': 'tree,form',
            'domain': [('visitor_id', '=', self.id)],
            'target': 'current',
        }
    
    def action_view_cosec_config(self):
        """Open COSEC configuration"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'COSEC Configuration',
            'res_model': 'frontdesk.cosec.config',
            'view_mode': 'tree,form',
            'target': 'current',
        }
