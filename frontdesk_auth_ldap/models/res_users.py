from odoo import _, api, fields, models, tools

class ResUser(models.Model):
    _inherit = 'res.users'

    created_by_azure = fields.Boolean(
        string='Created by LDAP',
        help='This user was created by LDAP.',
        default=False,
    )