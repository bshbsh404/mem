# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid
import ast

from werkzeug.urls import url_join
from datetime import datetime, timedelta

from odoo import models, fields, api, tools, _
from markupsafe import Markup

ASK_FIELDS_SELECTION = [
    ("required", "Required"),
    ("optional", "Optional"),
    ("none", "None"),
]

PLANNED_VISITOR_TIME = 45

class Frontdesk(models.Model):
    _name = 'frontdesk.frontdesk'
    _description = 'Frontdesk'
    _inherit = ['mail.alias.mixin']

    name = fields.Char('Frontdesk Name', required=True)
    responsible_ids = fields.Many2many('res.users', string='Responsibles', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    theme = fields.Selection(selection=[("light", "Light"), ("dark", "Dark")], default='light')
    image = fields.Image("Image")
    register_image = fields.Image("Register background Image")
    host_selection = fields.Boolean('Host Selection', groups='frontdesk.frontdesk_group_user')
    authenticate_guest = fields.Boolean('Authenticate Guest', default=True, groups='frontdesk.frontdesk_group_user')
    ask_phone = fields.Selection(string='Phone', selection=ASK_FIELDS_SELECTION, default='required', required=True)
    ask_company = fields.Selection(string='Organization', selection=ASK_FIELDS_SELECTION, default='optional', required=True)
    ask_email = fields.Selection(string='Email', selection=ASK_FIELDS_SELECTION, default='none', required=True)
    ask_first_name = fields.Selection(string='First Name', selection=ASK_FIELDS_SELECTION, default='none', required=True)
    ask_second_name = fields.Selection(string='Second Name', selection=ASK_FIELDS_SELECTION, default='none', required=True)
    ask_third_name = fields.Selection(string='Third Name', selection=ASK_FIELDS_SELECTION, default='none', required=True)
    ask_fourth_name = fields.Selection(string='Family Name', selection=ASK_FIELDS_SELECTION, default='none', required=True)
    ask_visitor_id = fields.Selection(string='Visitor ID', selection=ASK_FIELDS_SELECTION, default='none', required=True)
    ask_passport = fields.Selection(string='Visitor Passport', selection=ASK_FIELDS_SELECTION, default='none', required=True)
    ask_landline = fields.Selection(string='Landline', selection=ASK_FIELDS_SELECTION, default='none', required=True)

    ask_host_phone = fields.Selection(string='Host Phone', selection=ASK_FIELDS_SELECTION, default='none', required=True)
    ask_host_landline = fields.Selection(string='Host Landline', selection=ASK_FIELDS_SELECTION, default='none', required=True)

    group_reservations = fields.Boolean(string='Group Reservations', groups='frontdesk.frontdesk_group_user')
    group_reservations_description = fields.Text(string='Group Reservations Description', groups='frontdesk.frontdesk_group_user')
    group_reservations_attachment_id = fields.Binary(string="Group Reservations Attachment", attachment=True, groups='frontdesk.frontdesk_group_user')

    enable_qr_code_sms = fields.Boolean(string='Enable QR Code SMS')
    enable_reservation_ack_mail = fields.Boolean(string='Enable Reservation Acknowledgment Email')
    enable_reservation_security_mail = fields.Boolean(string='Enable Reservation Email Copy For Security Group')

    operating_unit_id = fields.Many2one(
        "operating.unit",
        "Operating Unit",
    )
    is_online = fields.Boolean("Is Online", default=False)
    allow_recaptcha = fields.Boolean("Allow Recaptcha", default=True)
    is_reception_desk = fields.Boolean("Is Reception Desk", default=False)
    security_employee_id = fields.Many2one('hr.employee', string='Security Employee')

    qr_code_sms_template_id = fields.Many2one(
        'sms.template',
        string='QR Code SMS Template',
        domain="[('model', '=', 'frontdesk.visitor')]",
        default=lambda self: self.env.ref('frontdesk.qr_code_sms_template', raise_if_not_found=False)
    )
    reservation_ack_mail_template_id = fields.Many2one(
        'mail.template',
        string='Reservation Acknowledgment Email Template',
        domain="[('model', '=', 'frontdesk.visitor')]",
        default=lambda self: self.env.ref('frontdesk.reservation_ack_mail_template', raise_if_not_found=False)
    )

    visitor_checkout_reminder_sms_template_id = fields.Many2one(
        'sms.template',
        string='Visitor Checkout Reminder SMS Template',
        domain="[('model', '=', 'frontdesk.visitor')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_sms_visitor_checkout_reminder_template', raise_if_not_found=False)
    )

    notify_email = fields.Boolean('Notify by email', groups='frontdesk.frontdesk_group_user')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain="[('model', '=', 'frontdesk.visitor')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_mail_template', raise_if_not_found=False)
    )
    host_mail_template_id = fields.Many2one(
        'mail.template',
        string='Host Approve email Template',
        domain="[('model', '=', 'frontdesk.request')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_host_approve_mail_template', raise_if_not_found=False)
    )
    notify_sms = fields.Boolean('Notify by SMS', groups='frontdesk.frontdesk_group_user')
    sms_template_id = fields.Many2one(
        'sms.template',
        string='SMS Template',
        domain="[('model', '=', 'frontdesk.frontdesk')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_sms_template', raise_if_not_found=False)
    )
    self_check_in = fields.Boolean('Self Check-In', groups='frontdesk.frontdesk_group_user',
        help='Shows a QR code in the interface, for guests to check in from their mobile phone.'
    )
    fullscreen_password = fields.Char('Fullscreen Password', groups='frontdesk.frontdesk_group_user')
    
    drink_offer = fields.Boolean('Offer Drinks', groups='frontdesk.frontdesk_group_user')
    drink_ids = fields.Many2many('frontdesk.drink')
    notify_discuss = fields.Boolean('Notify by discuss', default=True, groups='frontdesk.frontdesk_group_user')
    description = fields.Html(groups='frontdesk.frontdesk_group_user')
    visitor_ids = fields.One2many('frontdesk.visitor', 'station_id', string='Visitors')
    guest_on_site = fields.Integer('Guests On Site', compute='_compute_dashboard_data')
    pending = fields.Integer('Pending', compute='_compute_dashboard_data')
    drink_to_serve = fields.Integer('Drinks to Serve', compute='_compute_dashboard_data')
    latest_check_in = fields.Char(compute='_compute_dashboard_data')
    visitor_properties_definition = fields.PropertiesDefinition('Visitor Properties')
    access_token = fields.Char("Security Token", default=lambda self: str(uuid.uuid4()), required=True, copy=False, readonly=True)
    kiosk_url = fields.Char('Kiosk URL', compute='_compute_kiosk_url', groups='frontdesk.frontdesk_group_user')
    is_favorite = fields.Boolean()
    active = fields.Boolean(default=True)
    alias_id = fields.Many2one(
        help="The email address associated with this channel. New emails received will automatically create new leads assigned to the channel.")
    accept_from = fields.Selection([('all', 'Everyone'), ('specific', 'Specific Emails')], "Accept Emails From", default='all')
    email_ids = fields.One2many('frontdesk.email', 'station_id', string="Allowed Email Addresses")
    request_ids = fields.One2many('frontdesk.request', 'station_id')
    request_count = fields.Integer(compute='get_request_count')

    working_hours_start = fields.Float(string='Working Hours Start', default=7.0)
    working_hours_end = fields.Float(string='Working Hours End', default=15.0)
    email_host_domain = fields.Char(string='Host Email Domain', help='Host email domain to be used for host selection.', default="@owwsc.om")

    #### Reminder notification ####
    allow_reminder = fields.Boolean(string='Reminder Notification', default=True)
    reminder_notify_host_method = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Email and SMS')
    ], string='Reminder Notification Method for Host', default='both')
    reminder_notify_visitor_method = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Email and SMS')
    ], string='Reminder Notification Method for Visitor', default='both')
    reminder_notify_time = fields.Integer(string='Reminder Notification Time (minutes)', default=60)
    reminder_notify_host = fields.Boolean(string='Reminder for Host', default=True)
    reminder_notify_visitor = fields.Boolean(string='Reminder for Visitor', default=True)
    reminder_mail_visitor_template_id = fields.Many2one(
        'mail.template',
        string='Email Visitor Template',
        domain="[('model', '=', 'frontdesk.visitor')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_mail_visitor_reminder_template', raise_if_not_found=False)
    )
    reminder_mail_host_template_id = fields.Many2one(
        'mail.template',
        string='Email Host Template',
        domain="[('model', '=', 'hr.employee')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_mail_host_reminder_template', raise_if_not_found=False)
    )
    reminder_sms_visitor_template_id = fields.Many2one(
        'sms.template',
        string='SMS Visitor Template',
        domain="[('model', '=', 'frontdesk.frontdesk')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_sms_visitor_reminder_template', raise_if_not_found=False)
    )
    reminder_sms_host_template_id = fields.Many2one(
        'sms.template',
        string='SMS Host Template',
        domain="[('model', '=', 'frontdesk.frontdesk')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_sms_host_reminder_template', raise_if_not_found=False)
    )

    ### Late postpone notification ###
    postpone_time = fields.Integer(string='Postponement Time (minutes)', default=15)
    send_postpone_notification = fields.Boolean(string='Send Postponement Notification', default=True)
    postpone_notify_method = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Email and SMS')
    ], string='Postponement Notification Method', default='both')
    postpone_mail_template_id = fields.Many2one(
        'mail.template',
        string='Postponement Email Template',
        domain="[('model', '=', 'frontdesk.visitor')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_postpone_mail_template', raise_if_not_found=False)
    )
    postpone_sms_template_id = fields.Many2one(
        'sms.template',
        string='Postponement SMS Template',
        domain="[('model', '=', 'frontdesk.visitor')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_postpone_sms_template', raise_if_not_found=False)
    )

    # Users who can cancel all visits in case of extreme weather or crises.
    cancel_due_to_extreme_weather = fields.Boolean(string='Cancellation Due to Extreme Weather', default=True)
    
    cancellation_extreme_notify_method = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Email and SMS')
    ], string='Cancellation Notification Method (extreme weather)', default='both')
    cancellation_extreme_weather_mail_template_id = fields.Many2one(
        'mail.template',
        string='Cancellation Email Template',
        domain="[('model', '=', 'frontdesk.visitor')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_cancellation_extreme_weather_mail_template', raise_if_not_found=False)
    )
    cancellation_extreme_weather_sms_template_id = fields.Many2one(
        'sms.template',
        string='Cancellation SMS Template',
        domain="[('model', '=', 'frontdesk.visitor')]",
        default=lambda self: self.env.ref('frontdesk.frontdesk_cancellation_extreme_weather_sms_template', raise_if_not_found=False)
    )

    # enable or disable the extension of the visit
    allow_extend_visit = fields.Boolean(string='Allow Extension of Visit', default=True)
    # enable or disable the cancellation of the visit
    allow_cancel_visit = fields.Boolean(string='Allow Cancellation of Visit', default=True)
    # enable or disable the check-out of the visit
    allow_check_out = fields.Boolean(string='Allow Check-Out of Visit', default=True)

    absence_period = fields.Integer(string='Absence Period (minutes)', default=30, help="Time period after which a visitor is considered absent.")
    color = fields.Integer('Color Index', default=0)

    send_response_time_report = fields.Boolean(string='Send Late Response Report', default=True)
    response_time_limit = fields.Integer(
        string="Response Time Limit (minutes)",
        help="Time in minutes after which a response is considered late."
    )
    response_time_report_recipients = fields.Many2many(
        'res.users',
        string="Report Recipients",
        relation="frontdesk_report_recipients_rel",
        help="Users who will receive the late response report."
    )
    building_id = fields.Many2one('owwsc.building', string="Building")

    def _send_late_response_report(self):
        frontdesks = self.search([('send_response_time_report', '=', True), ('response_time_limit', '>', 0)])
        for frontdesk in frontdesks:
            late_transactions = self._get_late_responses(frontdesk)
            if late_transactions:
                self._send_late_response_report_email(frontdesk, late_transactions)

    def _get_late_responses(self, frontdesk):
        time_limit = timedelta(minutes=frontdesk.response_time_limit)
        late_responses = []

        requests = self.env['frontdesk.request'].search([
            ('station_id', '=', frontdesk.id),
        ])
        for request in requests:
            # use response_time, create_date, and time_limit to find late responses in frontdesk.request
            if request.response_time and request.create_date and time_limit:
                response_time = request.response_time
                create_date = request.create_date
                if response_time - create_date > time_limit:
                    late_responses.append(request)
        return late_responses

    def _send_late_response_report_email(self, frontdesk, late_transactions):
        template = self.env.ref('frontdesk.email_template_late_response_report')
        if template:
            template.with_context(late_transactions=late_transactions).send_mail(
                frontdesk.id,
                force_send=True
            )

    def _get_response_time_report_recipients_emails(self):
        """ Get comma-separated response_time_report_recipients email addresses. """
        self.ensure_one()
        return ",".join([e for e in self.response_time_report_recipients.mapped("email") if e])


    @api.depends('request_ids', 'request_ids.state')
    def get_request_count(self):
        for desk in self:
            desk.request_count = len(desk.request_ids.filtered(lambda r: r.state == 'draft'))
    def _compute_dashboard_data(self):
        """ This method computes the number of guests currently on site, the number of pending visitors, the number
        of drinks to serve, and the time of the latest check-in. """
        visitor_data = self.env['frontdesk.visitor']._read_group([
                ('state', 'in', ('checked_in', 'planned')),
                ('station_id', 'in', self.ids),
            ], ['station_id', 'state'], ['__count'])
        checked_in_mapped = {station.id: count for station, state, count in visitor_data if state == 'checked_in'}
        planned_mapped = {station.id: count for station, state, count in visitor_data if state == 'planned'}
        drinks_data = self.env['frontdesk.visitor']._read_group([
                ('drink_ids', '!=', False), ('served', '=', False),
                ('station_id', 'in', self.ids),
            ], ['station_id'], ['__count'])
        drinks_data_mapped = {station.id: count for station, count in drinks_data}
        for frontdesk in self:
            guest_on_site = pending = drink_to_serve = 0
            latest_check_in = False
            if frontdesk.visitor_ids:
                guest_on_site = checked_in_mapped.get(frontdesk.id, 0)
                pending = planned_mapped.get(frontdesk.id, 0)
                drink_to_serve = drinks_data_mapped.get(frontdesk.id, 0)
                last_visitors = frontdesk.visitor_ids.filtered(lambda v: v.state == 'checked_in')
                latest_check_in_time = last_visitors and last_visitors[-1].check_in
                if latest_check_in_time:
                    total_seconds = (datetime.now() - latest_check_in_time).total_seconds()
                    time_diff = int(total_seconds / 60) if total_seconds < 3600 else int(total_seconds / 3600)
                    latest_check_in = _("Last Check-In: %s minutes ago", time_diff) if total_seconds < 3600 \
                        else _("Last Check-In: %s hours ago", time_diff)
            frontdesk.update({
                'guest_on_site': guest_on_site,
                'pending': pending,
                'drink_to_serve': drink_to_serve,
                'latest_check_in': latest_check_in,
            })

    @api.depends('access_token')
    def _compute_kiosk_url(self):
        for frontdesk in self:
            frontdesk.kiosk_url = url_join(frontdesk.get_base_url(), '/kiosk/%s/%s' % (frontdesk.id, frontdesk.access_token))

    def action_open_kiosk(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.kiosk_url,
            'target': 'new',
        }

    def action_open_visitors(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Visitors"),
            'res_model': 'frontdesk.visitor',
            'view_mode': 'tree,form,kanban,graph,pivot,calendar,gantt',
            'context': {
                "search_default_state_is_planned": 1,
                "search_default_state_is_checked_in": 1,
                "search_default_today": 1,
                'default_station_id': self.id
            },
            'domain': [('station_id.id', '=', self.id)],
        }

    def action_open_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Requests"),
            'res_model': 'frontdesk.request',
            'view_mode': 'tree',
            'context': {'search_default_new': 1, 'default_station_id': self.id},
            'domain': [('station_id.id', '=', self.id)],
        }

    def _get_frontdesk_field(self):
        return ['description', 'host_selection', 'drink_offer', 'self_check_in', 'theme',
          'drink_ids', 'ask_email', 'ask_phone', 'ask_landline', 'ask_company', 'authenticate_guest',
          'allow_check_out', 'allow_cancel_visit', 'allow_extend_visit', 'ask_first_name',
          'ask_second_name', 'ask_third_name', 'ask_fourth_name', 'group_reservations', 'group_reservations_description', 'ask_visitor_id', 'ask_passport', 'ask_host_phone', 'ask_host_landline', 'working_hours_start', 'working_hours_end', 'email_host_domain', 'is_online', 'allow_recaptcha', 'fullscreen_password']

    def _get_frontdesk_data(self):
        """ Returns the data to the frontend. """
        self.ensure_one()
        return {
            'company': {'name': self.company_id.partner_id.name, 'id': self.company_id.id},
            'langs': [{'code': lang[0], 'name': lang[1]} for lang in self.env['res.lang'].get_installed()],
            'station': self.search_read([('id', '=', self.id)], self._get_frontdesk_field()),
        }

    def _get_planned_visitors(self):
        return []
        """ Returns the planned visitors for quick sign in to the frontend. """
        time_min = datetime.now() - timedelta(minutes=PLANNED_VISITOR_TIME)
        time_max = datetime.now() + timedelta(minutes=PLANNED_VISITOR_TIME)
        visitors = self.env['frontdesk.visitor'].sudo().search_read(
                [('check_in', '>=', time_min), ('check_in', '<=', time_max), ('state', '=', 'planned'), ('station_id.id', '=', self.id)],
                ['name', 'company', 'message', 'host_ids'])
        if visitors:
            return [{
                **visitor,
                'host_ids': [{'id': host.id, 'name': host.name} for host in self.env['hr.employee'].browse(visitor['host_ids'])]
            } for visitor in visitors]
        return []

    def _get_tmp_code(self):
        self.ensure_one()
        return tools.hmac(self.env(su=True), 'kiosk-mobile', (self.id, fields.Date.to_string(fields.Datetime.now())))

    # ------------------------------------------------------------
    # Mail Alias Mixin
    # ------------------------------------------------------------

    def _alias_get_creation_values(self):
        values = super(Frontdesk, self)._alias_get_creation_values()
        values['alias_model_id'] = self.env['ir.model']._get('frontdesk.request').id
        if self._origin.id:
            values['alias_defaults'] = defaults = ast.literal_eval(self.alias_defaults or "{}")
            defaults['station_id'] = self.id
            if not self.alias_name:
                values['alias_name'] = self.name.replace(' ', '-')
        return values

class FrontDeskAllowedEmail(models.Model):
    _name = 'frontdesk.email'
    _description = "Frontdesk: Allowed Email"

    station_id = fields.Many2one('frontdesk.frontdesk', ondelete="CASCADE")
    name = fields.Char(string="Email", required=True, index=True)
    state = fields.Selection([
        ('enable', 'Enabled'),
        ('disable', 'Disabled'),
    ], required=True, default='enable')