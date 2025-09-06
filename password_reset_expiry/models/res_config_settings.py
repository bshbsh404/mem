from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    signup_token_expiration_minutes = fields.Integer(
        string="Signup Token Expiration (Minutes)",
        default=20,
        config_parameter='auth_signup.token_expiration_minutes',
        help="Set the duration (in minutes) for which a password reset token remains valid."
    )