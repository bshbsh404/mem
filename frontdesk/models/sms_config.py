from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_nama_api_url = fields.Char(
        string="SMS API URL",
        config_parameter='sms.nama_api_url',
        default="https://i-messaging.com:7755/JSON/API/A2A/SendSMS"
    )
    sms_nama_method = fields.Selection(
        [('POST', 'POST'), ('GET', 'GET')],
        string="Method",
        config_parameter='sms.nama_method',
        default='POST'
    )
    sms_nama_media_type = fields.Char(
        string="Media Type",
        config_parameter='sms.nama_media_type',
        default="application/json"
    )
    sms_nama_bank_code = fields.Char(
        string="Bank Code",
        config_parameter='sms.nama_bank_code',
        default="NWS-VMS"
    )
    sms_nama_bank_pwd = fields.Char(
        string="Bank Password",
        config_parameter='sms.nama_bank_pwd',
        default="NWS@2024vms"
    )
    sms_nama_sender_id = fields.Char(
        string="Sender ID",
        config_parameter='sms.nama_sender_id',
        default="Nama Water"
    )
