# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Push notification USER_ID field
    push_user_id = fields.Integer(
        string='Push Notification User ID',
        help='User ID for push notification system. If not set, employee ID will be used.'
    )