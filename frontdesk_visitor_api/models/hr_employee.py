# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Add employee_number field if it doesn't exist in the base frontdesk module
    employee_number = fields.Char(string='Employee Number', help="Unique employee identifier")
    
    def get_pending_approvals(self):
        """Get pending visitor approvals for this employee"""
        self.ensure_one()
        
        # Find pending visitor requests where this employee is the host
        domain = [
            ('employee_id', '=', self.id),
            ('state', '=', 'planned'),
            ('date', '>=', fields.Date.today()),
        ]
        
        visitors = self.env['frontdesk.visitor'].sudo().search(domain)
        
        approvals = []
        for visitor in visitors:
            # Get the approval ID - using visitor ID as approval ID
            approval_id = f"A{visitor.id}"
            
            approvals.append({
                'visitor_name': visitor.partner_id.name,
                'approval_date': visitor.date.strftime('%Y-%m-%d') if visitor.date else '',
                'approval_time': visitor.check_in.strftime('%I:%M %p') if visitor.check_in else 'Pending',
                'purpose': visitor.purpose or 'Not specified',
                'approval_id': approval_id,
            })
        
        return approvals
    
    def approve_reject_visitor(self, approval_id, action):
        """Approve or reject a visitor request"""
        self.ensure_one()
        
        try:
            # Extract visitor ID from approval ID (format: A123)
            visitor_id = int(approval_id.replace('A', ''))
            
            # Find the visitor record
            visitor = self.env['frontdesk.visitor'].sudo().search([
                ('id', '=', visitor_id),
                ('employee_id', '=', self.id),
                ('state', '=', 'planned'),
            ], limit=1)
            
            if not visitor:
                return {
                    'validation_message': 'Visitor request not found or already processed',
                    'status': 'N'
                }
            
            # Process the action
            if action == 'approve':
                # In frontdesk module, approval might mean just keeping it as planned
                # or we could add a custom approval state/field
                visitor.write({'state': 'planned'})  # Keep as planned (approved)
                message = 'Visitor approved'
            elif action == 'reject':
                visitor.write({
                    'state': 'canceled',
                    'cancel_reason': 'Rejected by host'
                })
                message = 'Visitor rejected'
            else:
                return {
                    'validation_message': 'Invalid action. Use "approve" or "reject"',
                    'status': 'N'
                }
            
            return {
                'validation_message': message,
                'status': 'Y'
            }
            
        except (ValueError, TypeError):
            return {
                'validation_message': 'Invalid approval ID format',
                'status': 'N'
            }
        except Exception as e:
            return {
                'validation_message': f'Error processing request: {str(e)}',
                'status': 'N'
            }