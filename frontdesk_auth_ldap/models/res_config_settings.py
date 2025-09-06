from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    azure_ad_tenant_id = fields.Char(
        string="Azure Tenant ID",
        config_parameter="azure_ad.tenant_id",
        required=True,
    )
    azure_ad_client_id = fields.Char(
        string="Azure Client ID",
        config_parameter="azure_ad.client_id",
        required=True,
    )
    azure_ad_client_secret = fields.Char(
        string="Azure Client Secret",
        config_parameter="azure_ad.client_secret",
        required=True,
    )

    azure_user_id = fields.Many2one('res.users', string='Azure Template User',
        config_parameter="azure_ad.azure_user_id",
        required=True,
        help="User to copy when creating new users from Azure AD")