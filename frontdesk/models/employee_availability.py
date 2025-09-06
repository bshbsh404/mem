from odoo import models, fields, api

class EmployeeAvailability(models.Model):
    _name = 'employee.availability'
    _description = 'Employee Availability for Reservations'
    _inherit = 'mail.thread'

    name = fields.Many2one('hr.employee', string="Employee", required=True)
    availability_type = fields.Selection([
        ('available', 'Available'),
        ('on_leave', 'On Leave'),
        ('vacation', 'Vacation'),
        ('study_vacation', 'Study Vacation'),
        ('other', 'Other')
    ], string="Availability Type", required=True)
    start_date = fields.Datetime(string="Start Date", required=True)
    end_date = fields.Datetime(string="End Date", required=True)

    @api.model
    def create(self, vals):
        # Update availability in related visit requests when availability changes
        res = super(EmployeeAvailability, self).create(vals)
        res._update_employee_availability()
        return res

    def write(self, vals):
        # Update availability in related visit requests when availability changes
        res = super(EmployeeAvailability, self).write(vals)
        self._update_employee_availability()
        return res

    def _update_employee_availability(self):
        """Automatically create visit reassignment requests based on availability changes."""
        for availability in self:
            if availability.availability_type != 'available':
                # Find visits assigned to this employee within the specified period
                visits = self.env['frontdesk.request'].search([
                    ('employee_id', '=', availability.name.id),
                    ('planned_date', '>=', availability.start_date),
                    ('planned_date', '<=', availability.end_date),
                    ('state', 'in', ['draft', 'approve'])
                ])
                for visit in visits:
                    # Check if a reassignment request already exists for this visit
                    existing_request = self.env['visit.reassignment.request'].search([
                        ('request_id', '=', visit.id),
                        ('state', '=', 'pending')
                    ])
                    if not existing_request:
                        # Create a reassignment request
                        reassignment_request = self.env['visit.reassignment.request'].create({
                            'name': f'Reassignment Request for {visit.name}',
                            'request_id': visit.id,
                            'reason': f'Employee {availability.name.name} is unavailable ({availability.availability_type}).',
                            'type': 'request',
                            # 'current_employee_id': visit.employee_id.id
                        })
                        if reassignment_request:
                            # Notify all users in the 'group_visit_reassignment_manager' group
                            group = self.env.ref('frontdesk.group_visit_reassignment_manager')
                            if group:
                                users = group.users
                                notification_ids = [(0, 0,
                                {
                                    'res_partner_id': user.partner_id.id,
                                    'notification_type': 'inbox'
                                }) for user in users]
                                self.env['mail.message'].create({
                                    'message_type': "notification",
                                    'body': f"A reassignment has been requested for visit {visit.name} due to employee unavailability.",
                                    'subject': 'Visit Reassignment Request',
                                    'partner_ids': [(4, user.partner_id.id) for user in users],
                                    'model': 'visit.reassignment.request',
                                    'res_id': reassignment_request.id,
                                    'notification_ids': notification_ids,
                                    'author_id': self.env.user.partner_id and self.env.user.partner_id.id
                                })

                visitors = self.env['frontdesk.visitor'].search([
                    ('employee_id', '=', availability.name.id),
                    ('planned_date', '>=', availability.start_date),
                    ('planned_date', '<=', availability.end_date),
                    ('state', 'in', ['planned', 'extended', 'requested_extend', 'checked_in'])
                ])
                for visit in visitors:
                    # Check if a reassignment request already exists for this visit
                    existing_request = self.env['visit.reassignment.request'].search([
                        ('visit_id', '=', visit.id),
                        ('state', '=', 'pending')
                    ])
                    if not existing_request:
                        # Create a reassignment request
                        reassignment_request = self.env['visit.reassignment.request'].create({
                            'name': f'Visit Reassignment Request for {visit.partner_id.name if visit.partner_id else visit.id}',
                            'visit_id': visit.id,
                            'reason': f'Employee {availability.name.name} is unavailable ({availability.availability_type}).',
                            'type': 'approved_visit',
                            # 'current_employee_id': visit.employee_id.id
                        })
                        if reassignment_request:
                            # Notify all users in the 'group_visit_reassignment_manager' group
                            group = self.env.ref('frontdesk.group_visit_reassignment_manager')
                            if group:
                                users = group.users
                                notification_ids = [(0, 0,
                                {
                                    'res_partner_id': user.partner_id.id,
                                    'notification_type': 'inbox'
                                }) for user in users]
                                self.env['mail.message'].create({
                                    'message_type': "notification",
                                    'body': f"A reassignment has been requested for visit {'' if visit.partner_id else '#'}{visit.partner_id.name if visit.partner_id else visit.id} due to employee unavailability.",
                                    'subject': 'Visit Reassignment Request',
                                    'partner_ids': [(4, user.partner_id.id) for user in users],
                                    'model': 'visit.reassignment.request',
                                    'res_id': reassignment_request.id,
                                    'notification_ids': notification_ids,
                                    'author_id': self.env.user.partner_id and self.env.user.partner_id.id
                                })