# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class CosecController(http.Controller):

    @http.route('/frontdesk/cosec/send_visitor_data', type='json', auth='public', methods=['POST'])
    def send_visitor_data_to_cosec(self, visitor_id, **kwargs):
        """API endpoint to manually send visitor data to COSEC"""
        try:
            visitor = request.env['frontdesk.visitor'].sudo().browse(int(visitor_id))
            if not visitor.exists():
                return {'error': 'Visitor not found'}
            
            success = visitor._send_to_cosec_system()
            
            if success:
                return {
                    'success': True,
                    'message': 'Visitor data sent to COSEC successfully',
                    'visitor_id': visitor.id,
                    'emp_id': visitor.emp_id,
                    'qr_string': visitor.qr_string
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send visitor data to COSEC',
                    'visitor_id': visitor.id
                }
                
        except Exception as e:
            _logger.error(f"Error in send_visitor_data_to_cosec: {str(e)}")
            return {'error': str(e)}

    @http.route('/frontdesk/cosec/test_connection', type='json', auth='public', methods=['POST'])
    def test_cosec_connection(self, **kwargs):
        """Test connection to COSEC API"""
        try:
            config = request.env['frontdesk.cosec.config'].sudo().get_active_config()
            config.test_connection()
            return {'success': True, 'message': 'Connection test successful'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/frontdesk/cosec/get_logs', type='json', auth='public', methods=['POST'])
    def get_cosec_logs(self, visitor_id=None, limit=50, **kwargs):
        """Get COSEC logs for a visitor or all logs"""
        try:
            domain = []
            if visitor_id:
                domain.append(('visitor_id', '=', int(visitor_id)))
            
            logs = request.env['frontdesk.cosec.log'].sudo().search(
                domain, 
                limit=limit, 
                order='create_date desc'
            )
            
            log_data = []
            for log in logs:
                log_data.append({
                    'id': log.id,
                    'visitor_id': log.visitor_id.id,
                    'visitor_name': log.visitor_id.partner_id.name,
                    'emp_id': log.emp_id,
                    'qr_string': log.qr_string,
                    'state': log.state,
                    'api_url': log.api_url,
                    'response_data': log.response_data,
                    'error_message': log.error_message,
                    'create_date': log.create_date.strftime('%Y-%m-%d %H:%M:%S') if log.create_date else '',
                    'sent_date': log.sent_date.strftime('%Y-%m-%d %H:%M:%S') if log.sent_date else ''
                })
            
            return {'success': True, 'logs': log_data}
            
        except Exception as e:
            return {'error': str(e)}






