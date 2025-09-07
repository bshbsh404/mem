# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime, date
import base64
import io
import xlsxwriter


class VisitReportWizard(models.TransientModel):
    _name = 'visit.report.wizard'
    _description = 'Visit Report Wizard'

    date_from = fields.Date(string='From Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='To Date', required=True, default=fields.Date.today)
    station_id = fields.Many2one('frontdesk.frontdesk', string='Frontdesk Station', required=False)
    host_employee_id = fields.Many2one('hr.employee', string='Host Employee')
    report_file = fields.Binary(string='Report File', readonly=True)
    report_filename = fields.Char(string='Report Filename', readonly=True)
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from > record.date_to:
                raise models.ValidationError(_('From Date cannot be greater than To Date'))

    def action_generate_report(self):
        """Generate Excel report showing accepted and rejected visits by host employee"""
        # Build domain for filtering visits
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        
        # Station filter is now optional - if not selected, get all stations
        if self.station_id:
            domain.append(('station_id', '=', self.station_id.id))
        
        if self.host_employee_id:
            domain.append(('host_ids', 'in', [self.host_employee_id.id]))

        # Get all visits in the period
        visits = self.env['frontdesk.visitor'].search(domain)
        
        # Get all requests in the period for rejection tracking
        request_domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        if self.station_id:
            request_domain.append(('station_id', '=', self.station_id.id))
        if self.host_employee_id:
            request_domain.append(('employee_id', '=', self.host_employee_id.id))
            
        requests = self.env['frontdesk.request'].search(request_domain)
        
        # Group by host employee and station
        report_data = {}
        
        # Process visits
        for visit in visits:
            for host in visit.host_ids:
                key = (host.id, visit.station_id.id if visit.station_id else 0)
                if key not in report_data:
                    report_data[key] = {
                        'host_name': host.name,
                        'host_employee_number': host.employee_number if hasattr(host, 'employee_number') else '',
                        'station_name': visit.station_id.name if visit.station_id else 'No Station',
                        'accepted': 0,
                        'rejected': 0,
                        'total': 0
                    }
                
                if visit.state in ['checked_in', 'checked_out', 'finished', 'planned']:
                    report_data[key]['accepted'] += 1
                elif visit.state == 'canceled':
                    report_data[key]['rejected'] += 1
                    
                report_data[key]['total'] += 1
        
        # Process requests for rejected count
        for request in requests.filtered(lambda r: r.state == 'rejected'):
            if request.employee_id:
                key = (request.employee_id.id, request.station_id.id if request.station_id else 0)
                if key not in report_data:
                    report_data[key] = {
                        'host_name': request.employee_id.name,
                        'host_employee_number': request.employee_id.employee_number if hasattr(request.employee_id, 'employee_number') else '',
                        'station_name': request.station_id.name if request.station_id else 'No Station',
                        'accepted': 0,
                        'rejected': 0,
                        'total': 0
                    }
                report_data[key]['rejected'] += 1
                report_data[key]['total'] += 1

        # Generate Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Visit Report')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy',
            'align': 'center',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        number_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0'
        })
        
        # Title and period information
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # Merge cells for title
        worksheet.merge_range('A1:G1', 'Visit Report - Accepted and Rejected Visits by Host Employee', title_format)
        
        # Period information
        period_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center'
        })
        
        period_text = f"Period: {self.date_from.strftime('%d/%m/%Y')} to {self.date_to.strftime('%d/%m/%Y')}"
        if self.station_id:
            period_text += f" | Station: {self.station_id.name}"
        else:
            period_text += " | All Stations"
            
        worksheet.merge_range('A2:G2', period_text, period_format)
        
        # Add empty row
        worksheet.write('A3', '', cell_format)
        
        # Write headers
        headers = ['S.No', 'Host Employee Name', 'Employee Number', 'Station', 'Accepted Visits', 'Rejected Visits', 'Total Visits']
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
        
        # Set column widths
        worksheet.set_column('A:A', 8)  # S.No
        worksheet.set_column('B:B', 30)  # Host Employee Name
        worksheet.set_column('C:C', 20)  # Employee Number
        worksheet.set_column('D:D', 25)  # Station
        worksheet.set_column('E:E', 18)  # Accepted Visits
        worksheet.set_column('F:F', 18)  # Rejected Visits
        worksheet.set_column('G:G', 15)  # Total Visits
        
        # Write data
        row = 4
        s_no = 1
        total_accepted = 0
        total_rejected = 0
        total_visits = 0
        
        # Sort data by host name and station
        sorted_data = sorted(report_data.items(), key=lambda x: (x[1]['host_name'], x[1]['station_name']))
        
        for key, data in sorted_data:
            worksheet.write(row, 0, s_no, cell_format)
            worksheet.write(row, 1, data['host_name'], cell_format)
            worksheet.write(row, 2, data['host_employee_number'], cell_format)
            worksheet.write(row, 3, data['station_name'], cell_format)
            worksheet.write(row, 4, data['accepted'], number_format)
            worksheet.write(row, 5, data['rejected'], number_format)
            worksheet.write(row, 6, data['total'], number_format)
            
            total_accepted += data['accepted']
            total_rejected += data['rejected']
            total_visits += data['total']
            
            row += 1
            s_no += 1
        
        # Add totals row
        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E7E6E6',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0'
        })
        
        worksheet.merge_range(row, 0, row, 3, 'TOTAL', total_format)
        worksheet.write(row, 4, total_accepted, total_format)
        worksheet.write(row, 5, total_rejected, total_format)
        worksheet.write(row, 6, total_visits, total_format)
        
        workbook.close()
        
        # Get the Excel file
        excel_file = output.getvalue()
        output.close()
        
        # Encode the file
        report_data_file = base64.b64encode(excel_file)
        
        # Generate filename
        filename = f"visit_report_{self.date_from}_{self.date_to}.xlsx"
        
        # Update wizard with file
        self.write({
            'report_file': report_data_file,
            'report_filename': filename
        })
        
        # Return action to download the file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/report_file/{filename}?download=true',
            'target': 'self',
        }


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