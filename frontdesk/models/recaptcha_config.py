from odoo import models, fields

class RecaptchaResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    frontdesk_recaptcha_site_key = fields.Char(
        string="reCAPTCHA Site Key",
        config_parameter='frontdesk.recaptcha_site_key',
        default="6LfQy7QqAAAAAGzeeD5m3XVNAPT52R92NaX81-uX",
        help="Site key for Google reCAPTCHA. Used for rendering the reCAPTCHA widget."
    )
    frontdesk_recaptcha_secret_key = fields.Char(
        string="reCAPTCHA Secret Key",
        config_parameter='frontdesk.recaptcha_secret_key',
        default="6LfQy7QqAAAAAJJ8mf10okZO1pmtzmpnoU-G1EYJ",
        help="Secret key for Google reCAPTCHA. Used for verifying user actions."
    )