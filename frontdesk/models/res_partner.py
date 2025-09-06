from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_visitor = fields.Boolean("Is Visitor")
    is_blacklisted_from_visit = fields.Boolean(string="Blacklisted", default=False)
    passport_id = fields.Char(string="Passport ID")
    national_id = fields.Char(string="National/Resident ID")