from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class VisitPurpose(models.Model):
    _name = 'frontdesk.visit.purpose'
    _description = 'Visit Purpose'

    name = fields.Char(string="Purpose", required=True)
    department_ids = fields.Many2many('hr.department', string="Departments")
    is_other = fields.Boolean(string="Is Other")

    state_ids = fields.Many2many('owwsc.wilayat', string="Wilayat")

    other_reason_ids = fields.Many2many('frontdesk.other.reason', string="Other Reasons")

class OtherReason(models.Model):
    _name = 'frontdesk.other.reason'
    _description = 'Other Reason'

    name = fields.Char(string="Reason", required=True)