# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import qrcode
import base64
from io import BytesIO

from werkzeug.urls import url_encode, url_join
from markupsafe import Markup

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.http import request
import werkzeug.urls
import requests
from datetime import date, time
import logging

_logger = logging.getLogger(__name__)

class FrontdeskVisitor(models.Model):
    _name = 'frontdesk.visitor'
    _description = 'Frontdesk Visitors'
    _order = 'check_in'
    _rec_name = 'partner_id'

    active = fields.Boolean(default=True)
    parent_id = fields.Many2one('frontdesk.visitor', string="Main Visitor")
    child_ids = fields.One2many('frontdesk.visitor', 'parent_id', string="Child Visitors")
    child_count = fields.Boolean(compute='get_child_count')
    partner_id = fields.Many2one('res.partner', domain=[('is_visitor', '=', True), ('is_company', '=', False)], string='Visitor', required=True)
    phone = fields.Char('Phone', related='partner_id.phone')
    email = fields.Char('Email', related='partner_id.email')
    company_id = fields.Many2one('res.partner' ,'Visitor Company', related='partner_id.parent_id')
    message = fields.Html()
    host_ids = fields.Many2many('hr.employee', string='Host Name', domain="[('user_id', '!=', False)]")
    department_id = fields.Many2one('hr.department', string='Hosting Department')
    employee_id = fields.Many2one('hr.employee', string='Hosting Employee')
    drink_ids = fields.Many2many('frontdesk.drink', string='Drinks')
    date = fields.Date(string="Planned Date", required=True)
    check_in = fields.Datetime(string='Check In')
    check_out = fields.Datetime(string='Check Out')
    duration = fields.Float('Duration', compute="_compute_duration", store=True, default=1.0)
    extension = fields.Integer('Extension (minutes)', default=0)
    extension_status = fields.Selection([
        ('not_requested', 'Not Requested'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Extension Status', default='not_requested')
    wilayat_id = fields.Many2one('owwsc.wilayat', string="Wilayat")
    visit_type = fields.Selection(string='Visit Type',
        selection=[('employee', 'Employee'),
                   ('department', 'Department'),
                   ], 
        default='employee')
    is_online = fields.Boolean(string='Is Online')

    state = fields.Selection(string='Status',
        selection=[('planned', 'Planned'),
                   ('checked_in', 'Checked-In'),
                   ('requested_extend', 'Requested Extend'),
                   ('Extended', 'Extended'),
                   ('partially_checked_out', 'Partially Checked-Out'),
                   ('checked_out', 'Checked-Out'),
                   ('canceled', 'Canceled'),
                   ('finished', 'Finished'),
                   ('absent', 'Absent'),
                   ],
        default='planned'
    )
    source = fields.Selection([
        ('phone', 'Phone'),
        ('online', 'Online'),
        ('in_person', 'In Person'),
    ], string="Source", required=True, default='in_person')
    cancel_reason = fields.Text(string="Cancel Reason")
    is_finished = fields.Boolean(string="Is Finished?")
    
    station_id = fields.Many2one('frontdesk.frontdesk', required=True, string="Desk")
    visitor_properties = fields.Properties('Properties', definition='station_id.visitor_properties_definition', copy=True)
    served = fields.Boolean(string='Drink Served')
    qr_string = fields.Char(string='QR Code', default='/')
    qr_code = fields.Binary(compute='_generate_qr')
    belonging_ids = fields.One2many('frontdesk.belonging', 'visitor_id')

    planned_date = fields.Date(string="Planned Date")
    is_recurring = fields.Boolean(string='Is Recurring Visit?')
    planned_date_end = fields.Date(string='Planned End Date')
    planned_time = fields.Float(string="Planned Time")
    planned_duration = fields.Integer(string="Planned Duration (Minutes)")
    preferred_language = fields.Selection([
        ('en_US', 'English'),
        ('ar_001', 'Arabic'),
    ], string='Preferred Language', default='en_US')
    
    def get_planned_time_str(self):
        for rec in self:
            hour = int(rec.planned_time)
            minute = int((rec.planned_time - hour) * 60)
            return f"{hour:02}:{minute:02}"

    qr_code_download_link = fields.Char(string='QR Code Download Link')
    nfc_card_number = fields.Char(string='NFC Card Number', help="NFC Card number assigned to the visitor upon check-in.")
    evaluation = fields.Selection([
        ('very_sad', 'Very Sad 😡'),
        ('sad', 'Sad 🙁'),
        ('neutral', 'Neutral 😐'),
        ('happy', 'Happy 🙂'),
        ('very_happy', 'Very Happy 😃')
    ], string='Visitor Evaluation')
    evaluation_comment = fields.Text(string='Evaluation Comment')
    visit_purpose = fields.Text(string="Visit Purpose")
    emp_id = fields.Char(string="Employee ID")

    building_id = fields.Many2one('owwsc.building', string="Building")
    level_id = fields.Many2one('owwsc.level', string="Level")
    section_id = fields.Many2one('owwsc.section', string="Section")
    location_description = fields.Text(string="Location Description")
    
    same_building = fields.Boolean(string="Same Building", compute="_compute_same_building", store=True, index=True)
    @api.depends('building_id', 'station_id.building_id')
    def _compute_same_building(self):
        for rec in self:
            rec.same_building = rec.building_id and rec.station_id and rec.station_id.building_id and rec.building_id.id == rec.station_id.building_id.id

    accepted_employee_id = fields.Many2one('hr.employee', string="Accepted By")

    location_type = fields.Selection([
        ('meeting_hall', 'Meeting Hall'),
        ('office', 'Office'),
        ('department', 'Department')
    ], string="Location Type")

    owwsc_meeting_hall_id = fields.Many2one('owwsc.meeting_hall', string="Meeting Hall")
    owwsc_office_id = fields.Many2one('owwsc.office', string="Office")
    owwsc_department_id = fields.Many2one('owwsc.department', string="Department")
    other_reason_id = fields.Many2one('frontdesk.other.reason', string="Other Reason")

    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
        related="station_id.operating_unit_id",
    )

    # Add onchange to clear fields based on location type
    @api.onchange('location_type')
    def _onchange_location_type(self):
        if self.location_type == 'meeting_hall':
            self.owwsc_office_id = False
            self.owwsc_department_id = False
        elif self.location_type == 'office':
            self.owwsc_meeting_hall_id = False
            self.owwsc_department_id = False
        elif self.location_type == 'department':
            self.owwsc_meeting_hall_id = False
            self.owwsc_office_id = False

    def action_approve_extension(self):
       self.write({'extension_status': 'approved', 'planned_duration': self.planned_duration + self.extension})
    
    def action_reject_extension(self):
       self.write({'extension_status': 'rejected'})

    def _generate_qr(self):
        # method to generate QR code
        for rec in self:
            if qrcode and base64:

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=1,
                )
                qr.add_data(rec.qr_string)

                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({
                    'qr_code': qr_image,
                    })
                rec.update({
                    # 'qr_code_download_link': f'/web/content?model=frontdesk.visitor&id={rec.id}&field=qr_code'
                    'qr_code_download_link': f'/public/qr/{rec.id}'
                    })
                
            else:
                raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))

    def get_child_count(self):
        for visitor in self:
            visitor.child_count = len(visitor.child_ids)

    def write(self, vals):
        if vals.get('state') == 'checked_in':
            vals['check_in'] = fields.Datetime.now()
            self._notify()
            if self.drink_ids:
                self._notify_to_people()
        elif vals.get('state') == 'checked_out':
            vals['check_out'] = fields.Datetime.now()
            vals['served'] = True
        return super().write(vals)

    @api.depends('check_in', 'check_out')
    def _compute_duration(self):
        for visitor in self:
            if visitor.check_in and visitor.check_out:
                visitor.duration = (visitor.check_out - visitor.check_in).total_seconds() / 3600

    def action_check_in(self):
        self.ensure_one()
        self.state = 'checked_in'
        for child in self.child_ids.filtered(lambda c: c.state == 'planned'):
            child.action_check_in()

    def action_canceled(self):
        self.ensure_one()
        self.state = 'canceled'

    def action_request_extend_visit(self):
        self.ensure_one()
        self.extension_status = 'requested'

    def action_extend_visit(self, extension):
        self.ensure_one()
        self.extension = extension

    def action_finish(self):
        self.ensure_one()
        self.state = 'finished'
        self.is_finished = True
        # send sms notification to notify the visitor that the visit has ended and they should check out
        try:
            _logger.info('Sending frontdesk_sms_visitor_checkout_reminder_template SMS')
            sms_template = self.station_id.visitor_checkout_reminder_sms_template_id
            _logger.info(sms_template)
            if sms_template:
                _logger.info('Trying to Send frontdesk_sms_visitor_checkout_reminder_template SMS')
                body = sms_template._render_field('body', self.ids, compute_lang=True)[self.id]
                
                self.env['sms.sms'].create({
                    'body': body,
                    'number': self.phone,
                })._send(using_template=True)
        except Exception as e:
            _logger.error('Error sending frontdesk_sms_visitor_checkout_reminder_template SMS: %s', e)

    def action_check_out(self):
        self.ensure_one()

        # Check if the visit is recurring and the planned end date is set
        if self.is_recurring and self.planned_date_end:
            # Check if the planned end date is before today
            if self.planned_date_end < date.today():
                self.state = 'partially_checked_out'
            else:
                self.state = 'checked_out'
                self.is_finished = True
        else:
            self.state = 'checked_out'
            self.is_finished = True

        for child in self.child_ids.filtered(lambda c: c.state == 'checked_in'):
            child.action_check_out()

    def action_served(self):
        self.ensure_one()
        self.served = True

    def _notify(self):
        """ Send a notification to the frontdesk's responsible users and the visitor's hosts when the visitor checks in. """
        for visitor in self:
            msg = ""
            visitor_name = visitor.partner_id.display_name
            visitor_name += f" ({visitor.phone})" if visitor.phone else ""
            if visitor.station_id.responsible_ids:
                if visitor.host_ids:
                    host_info = ', '.join([f'{host.name}' for host in visitor.host_ids])
                    msg = visitor.station_id.name + _(" Check-In: %s to meet %s", visitor_name, host_info)
                else:
                    msg = visitor.station_id.name + _(" Check-In: %s", visitor_name)
                visitor._notify_by_discuss(visitor.station_id.responsible_ids, msg)
            if visitor.station_id.host_selection and visitor.host_ids:
                if visitor.station_id.notify_discuss:
                    msg = _("%s just checked-in.", visitor_name)
                    visitor._notify_by_discuss(visitor.host_ids, msg, True)
                if visitor.station_id.notify_sms:
                    visitor._notify_by_sms()

    def _notify_to_people(self):
        """ Send notification to the drink's responsible users when the visitor checks in. """
        for visitor in self:
            if visitor.drink_ids.notify_user_ids:
                action = visitor.env.ref('frontdesk.action_frontdesk_visitor').id
                url = url_encode({
                    'id': visitor.id,
                    'action': action,
                    'model': 'frontdesk.visitor',
                    'view_type': 'form',
                })
                name = f"{self.partner_id.display_name}"
                msg = _("%(name)s just checked-in. He requested %(drink)s.",
                    name=Markup('<a href="%s">%s</a>') % (url_join(visitor.get_base_url(), '/web?#%s' % url), name),
                    drink=', '.join(drink.name for drink in visitor.drink_ids),
                )
                visitor._notify_by_discuss(visitor.drink_ids.notify_user_ids, msg)

    def _notify_by_discuss(self, recipients, msg, is_host=False):
        for recipient in recipients:
            odoobot_id = self.env.ref("base.partner_root").id
            partners_to = [recipient.user_partner_id.id] if is_host else [recipient.partner_id.id]
            channel = self.env["discuss.channel"].with_user(SUPERUSER_ID).channel_get(partners_to)
            channel.message_post(body=msg, author_id=odoobot_id, message_type="comment", subtype_xmlid="mail.mt_comment")

    def _notify_by_email(self):
        _logger.info('Sending _notify_by_email email notification to visitor')
        try:
            if self.station_id.notify_email and self.station_id.mail_template_id:
                mail_template = self.station_id.mail_template_id
                if mail_template:
                    _logger.info('Sending email notification to visitor %s', self.partner_id.name)
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
            _logger.error('_notify_by_email Error sending email: %s', e)




    
    def _notify_by_sms(self):
        try:
            for host in self.host_ids:
                _logger.info('Sending SMS notification to host %s', host.name)
                if host.work_phone:
                    _logger.info('Sending SMS notification to host %s', host.work_phone)
                    sms_template = self.station_id.sms_template_id
                    body = sms_template._render_field('body', self.ids, compute_lang=True)[self.id]
                    _logger.info(sms_template)
                    _logger.info(body)

                    self.env['sms.sms'].create({
                        'body': body,
                        'number': host.work_phone,
                    })._send(using_template=True)
        except Exception as e:
            _logger.error('Error sending _notify_by_sms SMS: %s', e)

    ### Reminder Notification ###
    @api.model
    def send_reminder_notifications(self):
        _logger.info('Sending reminder notifications')
        now = fields.Datetime.now()
        visitors = self.search([
            ('state', '=', 'planned'),
            ('date', '=', fields.Date.today()),
        ])

        for visitor in visitors:
            frontdesk = visitor.station_id
            if visitor.planned_time is not None:
                planned_datetime = datetime.combine(visitor.planned_date, datetime.min.time()) + timedelta(hours=int(visitor.planned_time), minutes=(visitor.planned_time % 1) * 60)
                reminder_time = planned_datetime - timedelta(minutes=frontdesk.reminder_notify_time)
                if visitor.partner_id:
                    _logger.info('Visitor %s reminder time %s', visitor.partner_id.name, reminder_time)
                if frontdesk.allow_reminder and now >= reminder_time:
                    if visitor and frontdesk.reminder_notify_host:
                        self._send_reminder_host_notification(visitor)
                        _logger.info('Sent reminder to host')
                    if visitor and frontdesk.reminder_notify_visitor:
                        self._send_reminder_visitor_notification(visitor)
                        _logger.info('Sent reminder to visitor')

    def _send_reminder_host_notification(self, visitor):
        frontdesk = visitor.station_id
        method = frontdesk.reminder_notify_host_method
        for host in visitor.host_ids:
            if method in ['email', 'both'] and host.user_id.email:
                mail_template = frontdesk.reminder_mail_host_template_id
                if mail_template:
                    mail_template.send_mail(host.id, force_send=True)
            if method in ['sms', 'both'] and host.work_phone:
                if host.work_phone:
                    try:
                        sms_template = frontdesk.reminder_sms_host_template_id
                        body = sms_template._render_field('body', self.ids, compute_lang=True)[self.id]
                        
                        self.env['sms.sms'].create({
                            'body': body,
                            'number': host.work_phone,
                        })._send(using_template=True)
                    except Exception as e:
                        _logger.error('Error sending _send_reminder_host_notification SMS: %s', e)

                
    def _send_reminder_visitor_notification(self, visitor):
        frontdesk = visitor.station_id
        method = frontdesk.reminder_notify_visitor_method
        if method in ['email', 'both'] and visitor.email:
            mail_template = frontdesk.reminder_mail_visitor_template_id
            if mail_template:
                mail_template.send_mail(visitor.id, force_send=True)
        if method in ['sms', 'both'] and visitor.phone:
            if visitor.phone:
                try:
                    sms_template = frontdesk.reminder_sms_visitor_template_id
                    body = sms_template._render_field('body', self.ids, compute_lang=True)[self.id]
                    
                    self.env['sms.sms'].create({
                        'body': body,
                        'number': visitor.partner_id.phone if visitor.partner_id else visitor.phone,
                    })._send(using_template=True)
                except Exception as e:
                    _logger.error('Error sending _send_reminder_visitor_notification SMS: %s', e)

    ### Postponement Notification ###
    @api.model
    def send_postponement_notifications(self):
        _logger.info('Checking for visitors to postpone due to lateness')
        now = fields.Datetime.now()
        visitors = self.search([
            ('state', '=', 'planned'),
            ('date', '=', fields.Date.today()),
        ])

        for visitor in visitors:
            frontdesk = visitor.station_id
            if visitor.check_in and frontdesk.send_postpone_notification:
                postpone_time = visitor.check_in + timedelta(minutes=frontdesk.postpone_time)
                if now >= postpone_time:
                    _logger.info('Visitor %s is late, sending postponement notification', visitor.partner_id.name)
                    self._send_postponement_notification(visitor)

    def _send_postponement_notification(self, visitor):
        frontdesk = visitor.station_id
        method = frontdesk.postpone_notify_method
        if method in ['email', 'both'] and visitor.email:
            mail_template = frontdesk.postpone_mail_template_id
            if mail_template:
                mail_template.send_mail(visitor.id, force_send=True)
        if method in ['sms', 'both'] and visitor.phone:
            if visitor.phone:
                try:
                    sms_template = frontdesk.postpone_sms_template_id
                    body = sms_template._render_field('body', self.ids, compute_lang=True)[self.id]
                    
                    self.env['sms.sms'].create({
                        'body': body,
                        'number': visitor.partner_id.phone if visitor.partner_id else visitor.phone,
                    })._send(using_template=True)
                except Exception as e:
                    _logger.error('Error sending _send_postponement_notification SMS: %s', e)

    @api.model
    def cancel_all_visits_due_to_extreme_weather(self):
        _logger.info('Cancelling all visits due to extreme weather or crises')
        visitors = self.search([
            ('state', 'in', ['planned', 'checked_in']),
            ('date', '=', fields.Date.today()),
        ])

        for visitor in visitors:
            visitor.state = 'canceled'
            self._send_extreme_weather_cancellation_notification(visitor)

    def _send_extreme_weather_cancellation_notification(self, visitor):
        frontdesk = visitor.station_id
        method = frontdesk.cancellation_extreme_notify_method
        if method in ['email', 'both'] and visitor.email:
            mail_template = frontdesk.cancellation_extreme_weather_mail_template_id
            if mail_template:
                mail_template.send_mail(visitor.id, force_send=True)
        if method in ['sms', 'both'] and visitor.phone:
            if visitor.phone:
                try:
                    sms_template = frontdesk.cancellation_extreme_weather_sms_template_id
                    body = sms_template._render_field('body', self.ids, compute_lang=True)[self.id]
                    
                    self.env['sms.sms'].create({
                        'body': body,
                        'number': visitor.partner_id.phone if visitor.partner_id else visitor.phone,
                    })._send(using_template=True)
                except Exception as e:
                    _logger.error('Error sending _send_extreme_weather_cancellation_notification SMS: %s', e)
    
    ### Absence Checking ###
    @api.model
    def check_absent_visitors(self):
        now = fields.Datetime.now()
        visitors = self.search([
            ('state', '=', 'planned'),
            ('date', '<=', fields.Date.today()),
        ])
        for visitor in visitors:
            frontdesk = visitor.station_id
            if visitor.planned_time is not None:
                planned_datetime = datetime.combine(visitor.planned_date, datetime.min.time()) + timedelta(hours=int(visitor.planned_time), minutes=(visitor.planned_time % 1) * 60)
                absence_time = planned_datetime + timedelta(minutes=frontdesk.absence_period)
                if now >= absence_time:
                    visitor.state = 'absent'
            elif visitor.date < fields.Date.today():
                visitor.state = 'absent'
        
    
    @api.model
    def create(self, values):
        values['qr_string'] = self.env['ir.sequence'].next_by_code('frontdesk.visitor') or '/'
        rec = super(FrontdeskVisitor, self).create(values)
        frontdesk = rec.station_id
        try:
            _logger.info("sending QR Code SMS")
            if rec and frontdesk and frontdesk.enable_qr_code_sms and frontdesk.qr_code_sms_template_id and rec.partner_id:
                _logger.info("sending QR Code SMS template found")
                _logger.info(rec.partner_id)
                _logger.info(rec.partner_id.phone)
                sms_template = frontdesk.qr_code_sms_template_id
                _logger.info(sms_template)

                body = sms_template._render_field('body', [rec.id], compute_lang=True)[rec.id]

                _logger.info(body)
                if rec.partner_id:
                    self.env['sms.sms'].create({
                        'body': body,
                        'number': rec.partner_id.phone,
                    })._send(using_template=True)
            else:
                _logger.warning('QR Code SMS template not found for frontdesk %s', frontdesk.name)
                
        except Exception as e:
            _logger.error('Error sending QR Code SMS: %s', e)
            
        if rec and rec.station_id and rec.station_id.enable_reservation_ack_mail and rec.station_id.reservation_ack_mail_template_id:
            try:
                mail_template = rec.station_id.reservation_ack_mail_template_id
                if mail_template and rec.partner_id:
                    mail_template.send_mail(rec.id, force_send=True)
                    if rec.station_id.enable_reservation_security_mail:
                        # send to security group (responsible_ids)
                        for user in rec.station_id.responsible_ids:
                            # get the user's partner_id
                            partner = user.partner_id
                            if partner:
                                mail_template.send_mail(rec.id, force_send=True, email_values={
                                'author_id': self.create_uid.partner_id.id,
                                'auto_delete': True,
                                'email_from': self.env.company.email_formatted,
                                'email_to': partner.email,
                                'message_type': 'user_notification',
                            },)
            except Exception as e:
                _logger.error('Error sending Email: %s', e)
        return rec


class PersonalBelonging(models.Model):
    _name = 'frontdesk.belonging'
    _description = 'Personal Belongings'

    property_name = fields.Char(string="Property",  help='Employee belongings name')
    property_count = fields.Char(string="Count", help='Count of property')
    number = fields.Integer(compute='get_number', store=True, string="Sl")
    visitor_id = fields.Many2one('frontdesk.visitor', string="Visitor")
    permission = fields.Selection([
        ('0', 'Allowed'),
        ('1', 'Not Allowed'),
        ('2', 'Allowed With Permission'),
        ], 'Permission', required=True, index=True, default='0', tracking=True)
