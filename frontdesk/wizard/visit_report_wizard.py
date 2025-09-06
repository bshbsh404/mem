# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime, date


class VisitReportWizard(models.TransientModel):
    _name = 'visit.report.wizard'
    _description = 'Visit Report Wizard'

    date_from = fields.Date(string='From Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='To Date', required=True, default=fields.Date.today)
    station_id = fields.Many2one('frontdesk.frontdesk', string='Frontdesk Station')
    host_employee_id = fields.Many2one('hr.employee', string='Host Employee')
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from > record.date_to:
                raise models.ValidationError(_('From Date cannot be greater than To Date'))

    def action_generate_report(self):
        """Generate visit report showing accepted and rejected visits by host employee"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        
        if self.station_id:
            domain.append(('station_id', '=', self.station_id.id))
        
        if self.host_employee_id:
            domain.append(('host_ids', 'in', [self.host_employee_id.id]))

        # Get all visits in the period
        visits = self.env['frontdesk.visitor'].search(domain)
        
        # Group by host employee
        report_data = {}
        for visit in visits:
            for host in visit.host_ids:
                if host.id not in report_data:
                    report_data[host.id] = {
                        'host_name': host.name,
                        'accepted': 0,
                        'rejected': 0,
                        'total': 0
                    }
                
                if visit.state in ['checked_in', 'checked_out', 'finished']:
                    report_data[host.id]['accepted'] += 1
                elif visit.state == 'canceled':
                    report_data[host.id]['rejected'] += 1
                    
                report_data[host.id]['total'] += 1

        # Create tree view action with report data
        action = {
            'name': _('Visit Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'visit.report.line',
            'target': 'current',
            'context': {
                'search_default_date_from': self.date_from,
                'search_default_date_to': self.date_to,
            }
        }
        
        # Delete existing report lines and create new ones
        self.env['visit.report.line'].search([]).unlink()
        
        for host_id, data in report_data.items():
            self.env['visit.report.line'].create({
                'host_employee_id': host_id,
                'host_name': data['host_name'],
                'accepted_count': data['accepted'],
                'rejected_count': data['rejected'],
                'total_count': data['total'],
                'date_from': self.date_from,
                'date_to': self.date_to,
            })
        
        return action


class VisitReportLine(models.TransientModel):
    _name = 'visit.report.line'
    _description = 'Visit Report Line'
    
    host_employee_id = fields.Many2one('hr.employee', string='Host Employee')
    host_name = fields.Char(string='Host Name')
    accepted_count = fields.Integer(string='Accepted Visits')
    rejected_count = fields.Integer(string='Rejected Visits') 
    total_count = fields.Integer(string='Total Visits')
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')