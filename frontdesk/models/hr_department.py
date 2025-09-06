from odoo import models, fields, api


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    # operating_unit_id = fields.Many2one(
    #     "operating.unit",
    #     "Operating Unit",
    # )
    operating_unit_ids = fields.Many2many('operating.unit', string='Operating Unit', required=True)
