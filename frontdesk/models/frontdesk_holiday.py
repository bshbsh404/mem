from odoo import models, fields

class FrontdeskHoliday(models.Model):
    _name = 'frontdesk.holiday'
    _description = 'Holiday Configuration'

    name = fields.Char(string="Holiday Name", required=True)
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
