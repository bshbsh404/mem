# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.exceptions import UserError


class FrontdeskVisitor(models.Model):
    _inherit = 'frontdesk.visitor'
    
    @api.constrains('partner_id', 'state')
    def _check_blacklisted_visitor(self):
        """Prevent accepting visits from blacklisted visitors"""
        for visitor in self:
            if visitor.partner_id.is_blacklisted_from_visit and visitor.state in ['planned', 'checked_in']:
                raise UserError(_("Cannot accept visit from blacklisted visitor: %s") % visitor.partner_id.name)
    
    def action_check_in(self):
        """Override to check blacklist before check-in"""
        for visitor in self:
            if visitor.partner_id.is_blacklisted_from_visit:
                raise UserError(_("Cannot check-in blacklisted visitor: %s") % visitor.partner_id.name)
        return super(FrontdeskVisitor, self).action_check_in()