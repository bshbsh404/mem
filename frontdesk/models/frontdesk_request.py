from datetime import datetime
import pandas

try:
    import pandas as pd
except:
    raise UserWarning("This module requires pandas to be installed. Use command pip3 install pandas")
from io import BytesIO
import email.utils as email_utils
import werkzeug.urls
import logging
_logger = logging.getLogger(__name__)


from odoo import fields, models, api, _
from odoo.exceptions import UserError

class VisitRejectReason(models.Model):
    _name = 'visit.reject.reason'
    _description = 'Visit Reject Reason'
    name = fields.Char(string="Reason", required=True)

class VisitRequest(models.Model):
    _name = 'frontdesk.request'
    _inherit = ['mail.thread']
    _description = 'Visit Request'

    def get_default_station(self):
        return self.env['frontdesk.frontdesk'].search([], limit=1)
    
    def get_default_planned_time(self):
        # Default planned time
        # get current time
        # Get current time in Oman timezone (UTC+4)
        current_time = datetime.now().replace(tzinfo=None) + fields.Datetime.context_timestamp(self, datetime.now()).utcoffset()
        #  add 20 minutes to the current time
        current_time = current_time.replace(minute=current_time.minute + 20, second=0, microsecond=0)
        _logger.info(f"Current time: {current_time}")
        # convert to float time
        converted_time = current_time.hour + (current_time.minute / 60.0)
        _logger.info(f"Converted time: {converted_time}")
        _logger.info(f"Converted time after adding 1 hour: {converted_time}")
        
        return converted_time
    
    def get_default_planned_duration(self):
        # Default planned duration is 30 minutes
        return 30

    station_id = fields.Many2one('frontdesk.frontdesk', required=True, string="Desk", default=get_default_station)
    name = fields.Char(string="First Name", required=True, index=True)
    second_name = fields.Char(string="Second Name")
    third_name = fields.Char(string="Third Name")
    fourth_name = fields.Char(string="Family Name")
    full_name = fields.Char(string="Full Name", compute='_compute_full_name', store=True)
    visitor_id_number = fields.Char(string="Visitor ID")
    passport = fields.Char(string="Passport Number")
    visit_purpose = fields.Text(string="Visit Purpose")
    
    @api.depends('name', 'second_name', 'third_name', 'fourth_name')
    def _compute_full_name(self):
        for record in self:
            record.full_name = ' '.join(filter(None, [record.name, record.second_name, record.third_name, record.fourth_name]))

    source = fields.Selection([
        ('phone', 'Phone'),
        ('online', 'Online'),
        ('in_person', 'In Person'),
    ], string="Source", required=True, default='in_person')
    
    date = fields.Date(string="Planned Date")
    phone = fields.Char(index=True)
    landline = fields.Char(string="Landline")
    planned_date = fields.Date(string="Planned Date")
    is_recurring = fields.Boolean(string='Is Recurring Visit?')
    planned_date_end = fields.Date(string='Planned End Date')
    planned_time = fields.Float(string="Planned Time", default=get_default_planned_time)
    # 
    planned_duration = fields.Integer(string="Planned Duration (Minutes)", default=get_default_planned_duration)
    preferred_language = fields.Selection([
        ('en_US', 'English'),
        ('ar_001', 'Arabic'),
    ], string='Preferred Language', default='en_US')
    
    building_id = fields.Many2one('owwsc.building', string="Building")
    level_id = fields.Many2one('owwsc.level', string="Level")
    section_id = fields.Many2one('owwsc.section', string="Section")
    location_description = fields.Text(string="Location Description")
    request_visit_id = fields.Many2one('frontdesk.visitor', string="Visit")

    email = fields.Char()
    company = fields.Char()
    department = fields.Char()

    visitor_id = fields.Many2one('res.partner', string="Existing Visitor", domain=[('is_visitor', '=', True), ('is_company', '=', False)])
    company_id = fields.Many2one('res.partner', string="Existing Company", domain=[('is_visitor', '=', True), ('is_company', '=', True)])
    department_id = fields.Many2one('hr.department', string="Existing Department")
    employee_name = fields.Char(string="Employee Name")
    employee_phone = fields.Char(string="Employee Phone")
    host_landline = fields.Char(string="Employee Landline")
    employee_email = fields.Char(string="Employee Email")
    employee_id = fields.Many2one('hr.employee', string="Hosting Employee")
    emp_id = fields.Char(string="Employee ID")
    response_time = fields.Datetime(string="Response Time", readonly=True)
    other_reason_id = fields.Many2one('frontdesk.other.reason', string="Other Reason")
    wilayat_id = fields.Many2one('owwsc.wilayat', string="Wilayat")
    visit_type = fields.Selection(string='Visit Type',
        selection=[('employee', 'Employee'),
                   ('department', 'Department'),
                   ], 
        default='employee')
    is_online = fields.Boolean(string='Is Online')

    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
        # default=lambda self: self.station_id.operating_unit_id,
        domain="[('id', 'in', operating_unit_ids)]",
    )
    # a field to store the reason for operating unit change
    operating_unit_change_reason = fields.Many2one('frontdesk.operating.unit.change.reason', string="Operating Unit Change Reason")
      
    operating_unit_ids = fields.Many2many(
        "operating.unit",
        compute="_compute_operating_units",
        string="Available Operating Units",
    )   

    @api.depends('wilayat_id')
    def _compute_operating_units(self):
        for record in self:
            if record.wilayat_id:
                buildings = self.env['owwsc.building'].search([('wilayat_id', '=', record.wilayat_id.id)])
                record.operating_unit_ids = buildings.mapped('operating_unit_id')
            else:
                record.operating_unit_ids = self.env['operating.unit'].search([])

    # on change of operating_unit_id, change the station_id
    @api.onchange('operating_unit_id')
    def set_station_id(self):
        if self.operating_unit_id:
            # get the frontdesk for the operating unit
            st_operating_unit = self.env['frontdesk.frontdesk'].search([
                ('operating_unit_id', '=', self.operating_unit_id.id),
                ('is_reception_desk', '=', True),
            ], limit=1)
            if not st_operating_unit:
                st_operating_unit = self.env['frontdesk.frontdesk'].search([
                    ('operating_unit_id', '=', self.operating_unit_id.id)
                ], limit=1)
            if st_operating_unit:
                self.station_id = st_operating_unit.id
            
            
            # check if the reason for operating unit change is set
            if not self.operating_unit_change_reason:
                raise UserError(_("Please provide a reason for changing the operating unit."))

    # on change of employee_id, set the building, level, section and location description
    @api.onchange('employee_id')
    def set_employee_details(self):
        if self.employee_id:
            self.building_id = self.employee_id.building_id
            self.level_id = self.employee_id.level_id
            self.section_id = self.employee_id.section_id
            self.location_description = self.employee_id.location_description

    def get_visitor_approve_url(self):
        """Generates the approval URL for the host."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return werkzeug.urls.url_join(base_url, f'/frontdesk/approve_visitor/{self.id}')

    def get_visitor_reject_url(self):
        """Generates the rejection URL for the host."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return werkzeug.urls.url_join(base_url, f'/frontdesk/reject_visitor/{self.id}')
    
    def get_visitor_finish_url(self):
        """Generates the finish URL for the host."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return werkzeug.urls.url_join(base_url, f'/frontdesk/finish_visit/{self.id}')
    
    def get_planned_time_str(self):
        for rec in self:
            hour = int(rec.planned_time)
            minute = int((rec.planned_time - hour) * 60)
            return f"{hour:02}:{minute:02}"
        
    def _notify_host_by_email(self):
        _logger.info('Sending _notify_host_by_email email notification to host')
        try:
            if self.station_id.notify_email and self.station_id.host_mail_template_id:
                mail_template = self.station_id.host_mail_template_id
                _logger.info('Sending email notification to host start')
                if mail_template and self.employee_id:
                    _logger.info('Sending email notification to host %s', self.employee_id.name)
                    _logger.info('Sending email notification to id %s', self.id)
                    _logger.info('Sending email notification with template %s', mail_template)
                    if mail_template.model:
                        mail_template.sudo().send_mail(self.id, force_send=True)
                    else:
                        _logger.error('Mail template model is False. Cannot send email.')
                        raise UserError(_("Mail template model is not set. Cannot send email."))
                else:
                    _logger.warning('Mail template not found for frontdesk %s', self.station_id.name)
        except Exception as e:
            _logger.error('_notify_host_by_email Error sending email: %s', e)


    state = fields.Selection([
        ('draft', 'New'),
        ('approve', 'Approved'),
        ('rejected', 'Rejected')
    ], required=True, default='draft', readonly=True)
    reject_reason_id = fields.Many2one('visit.reject.reason', string="Rejection Reason", required=False)

    @api.onchange('visitor_id')
    def set_related_company(self):
        if self.visitor_id.parent_id:
            self.company_id = self.visitor_id.parent_id.id

    def action_create_visitor(self):
        for request in self:
            company = False
            if request.company_id:
                company = request.company_id
            elif request.company:
                company_vals = {
                    'is_visitor': True,
                    'is_company': True,
                    'name': request.company,
                }
                company = self.env['res.partner'].sudo().create(company_vals)
            visitor_vals = {
                'is_visitor': True,
                'name': request.name,
                'phone': request.phone,
                'email': request.email,
                'passport_id': request.passport,
                'national_id': request.visitor_id_number,
            }
            # if company:
            #     visitor_vals['parent_id'] = company.id

            visitor = self.env['res.partner'].sudo().create(visitor_vals)
            request.visitor_id = visitor.id
            if company:
                request.company_id = company.id

    def action_approve(self):
       self.create_visits()
       self.write({'state': 'approve', 'response_time': fields.Datetime.now()})
    
    def action_reject_portal(self, reject_reason_id):
        self.ensure_one()
        self.write({
            'response_time': fields.Datetime.now(),
            'reject_reason_id': reject_reason_id,
            'state': 'rejected'
            })

    def action_reject(self):
        self.ensure_one()
        self.write({'response_time': fields.Datetime.now()})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Visit Request',
            'view_mode': 'form',
            'res_model': 'frontdesk.request',
            'view_id': self.env.ref('frontdesk.view_visit_request_reject_form').id,
            'target': 'new',
            'res_id': self.id,
        }
    
    def confirm_reject(self):
        for request in self:
            if not request.reject_reason_id:
                raise UserError(_("Please provide a reason for rejection."))
            request.write({'state': 'rejected'})
    
    def send_email_to_host(self):
        for request in self.filtered(lambda r: r.state == 'draft'):
            try:
                _logger.info(f"Sending email notification to host for request {request.id}")
                if request.employee_id:
                    self._notify_host_by_email()
                else:
                    _logger.error(f"Error sending email notification to host: No employee found for request {request.name}")
                    raise UserError(_("Error sending email notification to host: No employee found for request %s" % request.name))
            except Exception as e:
                _logger.error(f"Error sending email notification for host: {e}")

    def create_visits(self):
        default_station = self.env['frontdesk.frontdesk'].search([], limit=1)
        for request in self.filtered(lambda r: r.state == 'draft'):
            if request.employee_id and not request.building_id:
                request.building_id = request.employee_id.building_id
            if request.employee_id and not request.level_id:
                request.level_id = request.employee_id.level_id
            if request.employee_id and not request.section_id:
                request.section_id = request.employee_id.section_id
            if request.employee_id and not request.location_description:
                request.location_description = request.employee_id.location_description

            if not request.visitor_id:
                raise UserError(f"Please set an existing visitor or create one for the visitor {request.name}")
            
            if request.visitor_id.is_blacklisted_from_visit:
                raise UserError((f"The visitor {request.name} is blacklisted and cannot be approved."))

            if not request.visitor_id.email:
                raise UserError(f"Please set an email for visitor {request.name}")

            if not request.date:
                raise UserError(f"Please set planned date for the visitor {request.name}")

            if not request.employee_id:
                raise UserError(f"Please set hosting employee for the visitor {request.name}")

            if not request.building_id:
                raise UserError(f"Please set building for the visitor {request.name}")
            
            if not request.level_id:
                raise UserError(f"Please set building level for the visitor {request.name}")
            
            if not request.section_id:
                raise UserError(f"Please set building section for the visitor {request.name}")
        
            station = request.station_id or default_station
            
            # get the current user as the accepted employee
            accepted_employee_id = False
            try:
                accepted_employee_id = self.env.user.employee_id.id
            except:
                _logger.error("Error getting current user employee id")

            vals = {
                'partner_id': request.visitor_id.id,
                'station_id': station.id,
                'department_id': request.department_id.id if request.department_id else False,
                'employee_id': request.employee_id.id,
                'is_recurring': request.is_recurring,
                'date': request.planned_date,
                'planned_date': request.planned_date,
                'planned_date_end': request.planned_date_end,
                'planned_time': request.planned_time,
                'planned_duration': request.planned_duration,
                'visit_purpose': request.visit_purpose,
                'other_reason_id': request.other_reason_id.id if request.other_reason_id else False,
                'emp_id': request.emp_id,
                'building_id': request.building_id.id,
                'level_id': request.level_id.id,
                'section_id': request.section_id.id,
                'location_description': request.location_description,
                'accepted_employee_id': accepted_employee_id,
                'source': request.source if request.source else 'in_person',
                'preferred_language': request.preferred_language if request.preferred_language else 'en_US',
            }

            # existing_company_visitor = self.env['frontdesk.visitor'].search([
            #     ('partner_id.parent_id', '=', request.visitor_id.parent_id.id),
            #     ('date', '=', request.date)
            # ], limit=1)

            # if existing_company_visitor:
            #     vals['parent_id'] = existing_company_visitor.id

            visitor = self.env['frontdesk.visitor'].create(vals)
            if visitor:
                try:
                    request.write({'request_visit_id': visitor.id})
                except Exception as e:
                    _logger.error(f"Error updating request with visitor id: {e}")
                    
                if request.visitor_id:
                    request.visitor_id.write({
                        'national_id': request.visitor_id_number,
                        'passport_id': request.passport,
                        })
            try:
                visitor._notify_by_email()
            except Exception as e:
                _logger.error(f"Error sending email notification for visitor: {e}")

  
    @api.model
    def message_new(self, msg_dict, custom_values=None):
        if not custom_values:
            custom_values = {}
        try:

            station = self.env['frontdesk.frontdesk'].sudo().browse(custom_values.get('station_id'))
            email_from = msg_dict.get('email_from')
            parsed_email = email_utils.parseaddr(email_from)
            email = parsed_email[1]
            # Enabled Emails on station
            enabled_emails = station.email_ids.filtered(lambda e: e.state == 'enable').mapped('name')

            if not station:
                station = self.get_default_station()

            if station.accept_from != 'all' and email not in enabled_emails:
                _logger.error(f"station {station.name} does not accept emails from {email}")
                raise UserError(f"Email is not allowed to create visit requests {email}")

            if msg_dict.get('attachments'):
                created_requests = self.create_requests_from_attachments(msg_dict['attachments'], custom_values)
                if created_requests and len(created_requests) > 1:
                    _logger.info(f"Multiple requests created from email {email}: {created_requests.ids}")
                    return created_requests[0]
                elif created_requests:
                    return created_requests
                else:
                    _logger.error(f"Error creating visit request from email {email}")
                    raise UserError(_("Error creating visit request from email %s" % email))
            
        except Exception as e:
            _logger.error(f"Error creating visit request from email: {e}")
            raise UserError(_("Error creating visit request from email: %s" % e))
        
        _logger.info(f"Creating visit request from email {email}")
        _logger.info(f"Creating visit request from email {msg_dict}")
        _logger.info(f"Creating visit request from email {custom_values}")

        return super(VisitRequest, self).message_new( msg_dict, custom_values=custom_values)

    def create_requests_from_attachments(self, attachments, custom_values):
        for attachment in attachments:
            # Get Dataframe
            excel_bytes = attachment.content
            bytes_io = BytesIO(excel_bytes)
            df = pd.read_excel(bytes_io)
            # Get list of records
            records = df.to_dict(orient='records')
            requests = []
            for record in records:
                data = {}
                if isinstance(custom_values, dict):
                    data = custom_values.copy()
                # Date
                record_date = record.get('Planned Date', False)
                if isinstance(record_date, pandas.Timestamp):
                    date = record_date.to_pydatetime().date()
                elif isinstance(record_date, str):
                    date = fields.Date.from_str(record_date)
                else:
                    date = fields.Date.today()

                data.update({
                    'name': record.get('Name', 'Undefined'),
                    'phone': record.get('Phone', 'Undefined'),
                    'email': record.get('Email', 'Undefined'),
                    'company': record.get('Company', 'Undefined'),
                    'department': record.get('Department', 'Undefined'),
                    'employee_phone': record.get('Employee Phone', 'Undefined'),
                    'employee_email': record.get('Employee Email', 'Undefined'),
                    'date': date,
                })

                requests.append(data)
            return self.sudo().create(requests)

    @api.model
    def create(self, values):
        # find existing visitor
        existing_visitor = False
        if values and values.get('name'):
            if values.get('passport') and values.get('visitor_id_number') and values.get('email'):
                existing_visitor = self.env['res.partner'].sudo().search([
                    '|', '|'
                    ('passport_id', '=', values.get('passport').strip()),
                    ('national_id', '=', str(values.get('visitor_id_number')).strip()),
                    ('email', '=', values.get('email').strip()),
                ], limit=1)
            if not existing_visitor and values.get('passport') and values.get('email'):
                existing_visitor = self.env['res.partner'].sudo().search([
                    '|',
                    ('passport_id', '=', values.get('passport').strip()),
                    ('email', '=', values.get('email').strip()),
                ], limit=1)
            if not existing_visitor and values.get('visitor_id_number') and values.get('email'):
                existing_visitor = self.env['res.partner'].sudo().search([
                    '|',
                    ('national_id', '=', str(values.get('visitor_id_number')).strip()),
                    ('email', '=', values.get('email').strip()),
                ], limit=1)
            if not existing_visitor and values.get('visitor_id_number'):
                existing_visitor = self.env['res.partner'].sudo().search([
                    ('national_id', '=', str(values.get('visitor_id_number')).strip()),
                ], limit=1)
            if not existing_visitor and values.get('passport'):
                existing_visitor = self.env['res.partner'].sudo().search([
                    ('passport_id', '=', values.get('passport').strip()),
                ], limit=1)
            if not existing_visitor and values.get('email'):
                existing_visitor = self.env['res.partner'].sudo().search([
                    ('email', '=', values.get('email').strip()),
                ], limit=1)

        if existing_visitor:
            values['visitor_id'] = existing_visitor.id
            if existing_visitor and existing_visitor.email and values.get('email') and values.get('email') != existing_visitor.email:
                # if the email is different, update the email
                existing_visitor.write({'email': values.get('email')})
            if existing_visitor and values.get('phone') and values.get('phone') != existing_visitor.phone:
                # if the email is different, update the email
                existing_visitor.write({'phone': values.get('phone')})

        # Update existing company if found
        if values.get('company'):
            existing_company = self.env['res.partner'].sudo().search(
                [('name', 'ilike', values.get('company').strip())], limit=1)
            if existing_company:
                values['company_id'] = existing_company.id

        # Update existing department if found
        existing_department = False
        if values.get('department'):
            existing_department = self.env['hr.department'].sudo().search(
                [('name', 'ilike', values.get('department').strip())], limit=1)
            if existing_department:
                values['department_id'] = existing_department.id

        # Update existing employee if found
        
        existing_employee = False
        if values.get('employee_email'):
            existing_employee = self.env['hr.employee'].sudo().search(['|',
                ('work_email', 'ilike', str(values.get('employee_email')).strip()),
                ('private_email', 'ilike', str(values.get('employee_email')).strip()),
            ], limit=1)
            if existing_employee:
                values['employee_id'] = existing_employee.id

        if values.get('employee_phone') and not existing_employee:
            existing_employee = self.env['hr.employee'].sudo().search(['|',
                ('work_phone', 'ilike', str(values.get('employee_phone')).strip()),
                ('mobile_phone', 'ilike', str(values.get('employee_phone')).strip()),
            ], limit=1)
            if existing_employee:
                values['employee_id'] = existing_employee.id

        # if employee_id is set, set the building, level, section and location description
        if values.get('employee_id'):
            employee = self.env['hr.employee'].sudo().browse(values.get('employee_id'))
            if employee:
                values['building_id'] = employee.building_id.id
                values['level_id'] = employee.level_id.id
                values['section_id'] = employee.section_id.id
                values['location_description'] = employee.location_description

        if values.get('is_online') and values.get('is_online') == True:
            # Handling online requests automatic assignment
            _logger.info('Handling online requests automatic assignment')
            if values.get('visit_type') and values.get('visit_type') == 'employee':
                _logger.info('Creating online visit request for employee')
                # get the employee
                try:
                    employee = False
                    # reset the department_id to False
                    values['department_id'] = False

                    if not employee and values.get('employee_id'):
                        employee = self.env['hr.employee'].sudo().browse(values.get('employee_id'))

                    if not employee and values.get('employee_email'):
                        employee = self.env['hr.employee'].sudo().search(['|',
                            ('work_email', 'ilike', str(values.get('employee_email')).strip()),
                            ('private_email', 'ilike', str(values.get('employee_email')).strip()),
                        ], limit=1)

                    if not employee and values.get('employee_phone'):
                        employee = self.env['hr.employee'].sudo().search(['|',
                                ('work_phone', 'ilike', str(values.get('employee_phone')).strip()),
                                ('mobile_phone', 'ilike', str(values.get('employee_phone')).strip()),
                            ], limit=1)
                        
                    if employee:
                        # get the employee operating unit
                        employee_building_id = employee.building_id
                        employee_operating_unit = employee_building_id.operating_unit_id if employee_building_id else False
                        if employee_operating_unit:
                            # get desk for the operating unit with is_reception_desk == True
                            employee_desk = self.env['frontdesk.frontdesk'].search([
                                ('operating_unit_id', '=', employee_operating_unit.id),
                                ('is_reception_desk', '=', True),
                            ], limit=1)
                            if not employee_desk:
                                employee_desk = self.env['frontdesk.frontdesk'].search([
                                    ('operating_unit_id', '=', employee_operating_unit.id),
                                ], limit=1)
                            if employee_desk:
                                values['station_id'] = employee_desk.id
                                operating_unit_change_reason = self.env['frontdesk.operating.unit.change.reason'].search([
                                    ('name', '=', 'Automatic'),
                                ], limit=1)
                                if not operating_unit_change_reason:
                                    operating_unit_change_reason = self.env['frontdesk.operating.unit.change.reason'].create({
                                        'name': 'Automatic',
                                    })
                                values['operating_unit_change_reason'] = operating_unit_change_reason.id if operating_unit_change_reason else False
                                values['operating_unit_id'] = employee_desk.operating_unit_id.id if employee_desk.operating_unit_id else False
                except Exception as e:
                    _logger.error('Error creating online visit request for employee: %s', e)
                    
            elif values.get('visit_type') and values.get('visit_type') == 'department':
                _logger.info('Creating online visit request for department')
                try:
                    if values.get('department_id'):
                        department = self.env['hr.department'].sudo().browse(values.get('department_id'))
                    elif existing_department:
                        department = existing_department

                    _logger.info(values.get('department_id'))

                    if department:
                        _logger.info(department)
                        department_operating_unit = department.operating_unit_ids
                        _logger.info(department_operating_unit)

                        if department_operating_unit and len(department_operating_unit.ids) == 1:
                            _logger.info('Single operating unit found for department')
                            # get desk for the operating unit with is_reception_desk == True
                            department_desk = self.env['frontdesk.frontdesk'].search([
                                ('operating_unit_id', 'in', department_operating_unit.ids),
                                ('is_reception_desk', '=', True),
                            ], limit=1)
                            if not department_desk:
                                department_desk = self.env['frontdesk.frontdesk'].search([
                                    ('operating_unit_id', 'in', department_operating_unit.ids),
                                ], limit=1)
                            if department_desk:
                                values['station_id'] = department_desk.id
                                values['operating_unit_id'] = department_desk.operating_unit_id.id if department_desk.operating_unit_id else False
                        elif department_operating_unit and len(department_operating_unit.ids) > 1:
                            _logger.info('Multiple operating units found for department')
                            # get the selected wilayat_id
                            if 'wilayat_id' in values and values.get('wilayat_id'):
                                _logger.info('Getting selected wilayat_id')
                                try:
                                    selected_wilayat_id = self.env['owwsc.wilayat'].sudo().browse(int(values.get('wilayat_id')))
                                    if selected_wilayat_id:
                                        _logger.info("selected_wilayat_id")
                                        _logger.info(selected_wilayat_id)
                                        _logger.info(selected_wilayat_id.id)
                                        # get all the buildings in the wilayat
                                        buildings = self.env['owwsc.building'].search([
                                            ('wilayat_id', '=', selected_wilayat_id.id),
                                        ])
                                        _logger.info("buildings")
                                        _logger.info(buildings)
                                        if buildings and len(buildings.ids) == 1:
                                            # get the operating unit for the building
                                            building = buildings[0]
                                            if building:
                                                building_operating_unit = building.operating_unit_id
                                                if building_operating_unit:
                                                    _logger.info("building_operating_unit")
                                                    _logger.info(building_operating_unit)
                                                    values['operating_unit_id'] = building_operating_unit.id
                                                    department_desk = self.env['frontdesk.frontdesk'].search([
                                                        ('operating_unit_id', '=', building_operating_unit.id),
                                                        ('is_reception_desk', '=', True),
                                                    ], limit=1)
                                                    if not department_desk:
                                                        department_desk = self.env['frontdesk.frontdesk'].search([
                                                            ('operating_unit_id', '=', building_operating_unit.id),
                                                        ], limit=1)
                                                    if department_desk:
                                                        values['station_id'] = department_desk.id

                                except Exception as e:
                                    _logger.error('Error getting selected wilayat_id: %s', e)


                except Exception as e:
                    _logger.error('Error creating online visit request for department: %s', e)

        if not values.get('is_online') or not values.get('is_online') == True:
            try:
                if values.get('employee_id') and values.get('visit_type') == 'employee':
                    values['department_id'] = False
                    try:
                        employee = self.env['hr.employee'].sudo().browse(values.get('employee_id'))
                        if employee and employee.department_id:
                            values['department_id'] = employee.department_id.id
                    except Exception as e:
                        _logger.error('Error setting department_id for employee: %s', e)
            except Exception as e:
                _logger.error('Error creating normal visit request for employee: %s', e)

        _logger.info(f"before department_id: {values.get('department_id') if values.get('department_id') else None}")
        if 'department_id' in values:
            department = self.env['hr.department'].sudo().browse(values.get('department_id'))
            if not department.exists():
                values['department_id'] = False
        else:
            values['department_id'] = False
        _logger.info(f"Resolved department_id: {values.get('department_id') if values.get('department_id') else None}")


        _logger.info('Creating visit request with values model')
        _logger.info(values)

        return super(VisitRequest, self).create(values)
    

class FrontdeskRequestOperatingUnitChangeReason(models.Model):
    _name = 'frontdesk.operating.unit.change.reason'
    _description = 'Visit Request Operating Unit Change Reason'

    name = fields.Char(string="Reason", required=True)
