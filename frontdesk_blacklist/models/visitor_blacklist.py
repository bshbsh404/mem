# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime


class VisitorBlacklist(models.Model):
    _name = 'visitor.blacklist'
    _description = 'Visitor Blacklist'
    _order = 'create_date desc'

    partner_id = fields.Many2one('res.partner', string='Visitor', required=True, domain=[('is_visitor', '=', True)])
    user_id = fields.Many2one('res.users', string='Blacklisted By', required=True, default=lambda self: self.env.user)
    blacklist_date = fields.Datetime(string='Blacklist Date/Time', required=True, default=fields.Datetime.now)
    blacklist_reason = fields.Text(string='Blacklist Reason', required=True)
    active = fields.Boolean(string='Active', default=True)
    
    # Visitor information (for easy access)
    visitor_name = fields.Char(related='partner_id.name', string='Visitor Name', store=True)
    visitor_email = fields.Char(related='partner_id.email', string='Email', store=True)
    visitor_phone = fields.Char(related='partner_id.phone', string='Phone', store=True)
    visitor_id_number = fields.Char(related='partner_id.national_id', string='ID Number', store=True)
    
    def action_remove_from_blacklist(self):
        """Remove visitor from blacklist"""
        for record in self:
            record.active = False
            record.partner_id.is_blacklisted_from_visit = False
    
    def action_add_to_blacklist(self):
        """Add visitor to blacklist"""
        for record in self:
            record.active = True
            record.partner_id.is_blacklisted_from_visit = True
            
    @api.model
    def create(self, vals):
        """Override create to automatically blacklist the visitor"""
        record = super(VisitorBlacklist, self).create(vals)
        if record.active:
            record.partner_id.is_blacklisted_from_visit = True
        return record