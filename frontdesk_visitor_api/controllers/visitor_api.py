# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class VisitorApiController(http.Controller):

    @http.route('/api/visitor/approvals', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def get_visitor_approvals(self, **kwargs):
        """
        API endpoint to retrieve list of approvals for a user
        Input: {"employee_number": "12345"}
        Output: {"approvals": [{"visitor_name": "John Doe", ...}]}
        """
        try:
            # Get the data from request
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else kwargs
            employee_number = data.get('employee_number')
            
            if not employee_number:
                return {
                    'error': 'Missing employee_number parameter',
                    'approvals': []
                }
            
            # Find employee by employee_number
            employee = request.env['hr.employee'].sudo().search([
                ('employee_number', '=', employee_number)
            ], limit=1)
            
            if not employee:
                # Try to find by ID if employee_number is not found
                try:
                    employee_id = int(employee_number)
                    employee = request.env['hr.employee'].sudo().browse(employee_id)
                    if not employee.exists():
                        employee = False
                except ValueError:
                    employee = False
            
            if not employee:
                return {
                    'error': f'Employee with number {employee_number} not found',
                    'approvals': []
                }
            
            # Get pending approvals
            approvals = employee.get_pending_approvals()
            
            _logger.info(f"Retrieved {len(approvals)} approvals for employee {employee_number}")
            
            return {
                'approvals': approvals
            }
            
        except Exception as e:
            _logger.error(f"Error in get_visitor_approvals: {str(e)}")
            return {
                'error': str(e),
                'approvals': []
            }

    @http.route('/api/visitor/approve-reject', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def approve_reject_visitor(self, **kwargs):
        """
        API endpoint to approve/reject a visitor
        Input: {"employee_number": "12345", "approve_reject_flag": "approve", "approval_id": "A123"}
        Output: {"validation_message": "Visitor approved/rejected", "status": "Y"}
        """
        try:
            # Get the data from request
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else kwargs
            employee_number = data.get('employee_number')
            approve_reject_flag = data.get('approve_reject_flag')
            approval_id = data.get('approval_id')
            
            # Validate required parameters
            if not employee_number:
                return {
                    'validation_message': 'Missing employee_number parameter',
                    'status': 'N'
                }
            
            if not approve_reject_flag:
                return {
                    'validation_message': 'Missing approve_reject_flag parameter',
                    'status': 'N'
                }
                
            if not approval_id:
                return {
                    'validation_message': 'Missing approval_id parameter',
                    'status': 'N'
                }
            
            # Validate approve_reject_flag
            if approve_reject_flag not in ['approve', 'reject']:
                return {
                    'validation_message': 'Invalid approve_reject_flag. Use "approve" or "reject"',
                    'status': 'N'
                }
            
            # Find employee
            employee = request.env['hr.employee'].sudo().search([
                ('employee_number', '=', employee_number)
            ], limit=1)
            
            if not employee:
                # Try to find by ID if employee_number is not found
                try:
                    employee_id = int(employee_number)
                    employee = request.env['hr.employee'].sudo().browse(employee_id)
                    if not employee.exists():
                        employee = False
                except ValueError:
                    employee = False
            
            if not employee:
                return {
                    'validation_message': f'Employee with number {employee_number} not found',
                    'status': 'N'
                }
            
            # Process approval/rejection
            result = employee.approve_reject_visitor(approval_id, approve_reject_flag)
            
            _logger.info(f"Employee {employee_number} {approve_reject_flag}d visitor {approval_id}: {result}")
            
            return result
            
        except Exception as e:
            _logger.error(f"Error in approve_reject_visitor: {str(e)}")
            return {
                'validation_message': f'Error processing request: {str(e)}',
                'status': 'N'
            }