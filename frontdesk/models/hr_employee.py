from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    building_id = fields.Many2one('owwsc.building', string="Building")
    level_id = fields.Many2one('owwsc.level', string="Level")
    section_id = fields.Many2one('owwsc.section', string="Section")
    location_description = fields.Char(string="Location Description")