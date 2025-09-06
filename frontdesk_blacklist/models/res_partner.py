# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_blacklisted_from_visit = fields.Boolean(string='Blacklisted from Visits', default=False)
    blacklist_ids = fields.One2many('visitor.blacklist', 'partner_id', string='Blacklist Records')
    blacklist_count = fields.Integer(string='Blacklist Count', compute='_compute_blacklist_count')
    
    @api.depends('blacklist_ids')
    def _compute_blacklist_count(self):
        for partner in self:
            partner.blacklist_count = len(partner.blacklist_ids.filtered('active'))
    
    def action_blacklist_visitor(self):
        """Open blacklist wizard for this visitor"""
        return {
            'name': _('Blacklist Visitor'),
            'type': 'ir.actions.act_window',
            'res_model': 'visitor.blacklist.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
            }
        }
    
    def action_view_blacklist_records(self):
        """View all blacklist records for this visitor"""
        return {
            'name': _('Blacklist Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'visitor.blacklist',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }