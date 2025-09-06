from odoo import models, fields, api

class VisitReassignmentRequest(models.Model):
    _name = 'visit.reassignment.request'
    _description = 'Visit Reassignment Request'
    _inherit = 'mail.thread'

    name = fields.Char(string="Request Name", default='New Reassignment Request', readonly=True, required=True)
                
    request_id = fields.Many2one('frontdesk.request', string="Request")
    visit_id = fields.Many2one('frontdesk.visitor', string="Visit")
    type = fields.Selection([
        ('request', 'Visit Request'),
        ('approved_visit', 'Approved Visit'),
    ], string="Reassignment Type", required=True, default='request')
    current_employee_id = fields.Many2one('hr.employee', string="Current Employee")
    new_employee_id = fields.Many2one('hr.employee', string="New Employee")
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="State", default='pending', required=True)
    reason = fields.Text(string="Reason for Reassignment")

    def action_approve(self):
        self.ensure_one()
        self.state = 'approved'
        if self.new_employee_id:
            if self.type == 'request':
                self.request_id.employee_id = self.new_employee_id
            else:
                self.visit_id.employee_id = self.new_employee_id

    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'
