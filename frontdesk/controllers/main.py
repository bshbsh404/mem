# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, fields
from odoo.http import request, content_disposition
from odoo.tools import consteq
from datetime import datetime, timedelta, time
import requests
from pytz import timezone
import logging
import base64

_logger = logging.getLogger(__name__)


class QRCodeController(http.Controller):

    @http.route('/public/qr/<int:visitor_id>', type='http', auth='public', cors='*', website=True)
    def public_qr(self, visitor_id, **kwargs):
        visitor = request.env['frontdesk.visitor'].sudo().browse(visitor_id)
        if visitor.qr_code:
            qr_code_data = base64.b64decode(visitor.qr_code)
            headers = [
                ('Content-Type', 'image/png'),
                ('Content-Disposition', content_disposition(f'qr_code_{visitor_id}.png'))
            ]
            return request.make_response(qr_code_data, headers)
        return request.not_found()
    
class Frontdesk(http.Controller):
    def _get_additional_info(self, frontdesk, lang, is_mobile=False):
        return request.render('frontdesk.frontdesk', {
            'frontdesk': frontdesk,
            'is_mobile': is_mobile,
            'current_lang': lang,
        })
        
    def _get_azure_ad_token(self):
        config = request.env['ir.config_parameter'].sudo()
        tenant_id = config.get_param('azure_ad.tenant_id')
        client_id = config.get_param('azure_ad.client_id')
        client_secret = config.get_param('azure_ad.client_secret')

        if not all([tenant_id, client_id, client_secret]):
            return None

        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': 'https://graph.microsoft.com/.default',
        }

        try:
            response = requests.post(url, data=data)
            _logger.info(response.text)
            response.raise_for_status()
            return response.json().get("access_token")
        except requests.exceptions.RequestException:
            return None
        
    def _get_azure_ad_users(self, access_token):
        """
        Fetch all users from Azure AD using the Graph API.
        """
        # graph_url = "https://graph.microsoft.com/v1.0/users"
        graph_url = "https://graph.microsoft.com/v1.0/users?$select=mail,displayName,businessPhones,jobTitle,mobilePhone,officeLocation,department"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        all_users = []
        while graph_url:
            try:
                response = requests.get(graph_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                all_users.extend(data.get("value", []))  # Add the current batch of users

                # Check if there is a next page
                graph_url = data.get("@odata.nextLink")  # URL for the next page
            except requests.exceptions.RequestException as e:
                _logger.error("Error fetching Azure AD users: %s", e, exc_info=True)
                break

        return all_users
        
    def _get_ad_user_by_email(self, token, email):
        users = self._get_azure_ad_users(token)
        for user in users:
            try:
                if user.get("mail", "").lower() == email.lower():
                    return user
            except Exception as e:
                _logger.error(f"Error processing user {user.get('displayName', 'Unknown')}: {str(e)}")
        return False

    @http.route('/frontdesk/get_employee_info', type='json', auth='public', csrf=False)
    def get_employee_info(self, emp_id):
        employee = request.env['hr.employee'].sudo().search([('barcode', '=', emp_id)], limit=1)
        if not employee:
            return {'error': 'Not found'}
        # Split the full name into parts
        name_parts = employee.name.split() if employee.name else []
        first_name = ''
        second_name = ''
        third_name = ''
        fourth_name = ''
        
        # Handle names with different number of parts
        if len(name_parts) >= 4:
            first_name = name_parts[0]
            second_name = name_parts[1] if len(name_parts) > 1 else ''
            third_name = name_parts[2] if len(name_parts) > 2 else ''
            # Join all remaining parts as the fourth name
            fourth_name = ' '.join(name_parts[3:]) if len(name_parts) > 3 else ''
        else:
            # Ensure we have at least 4 parts, filling missing ones with empty strings
            while len(name_parts) < 4:
                name_parts.append('')
            first_name = name_parts[0]
            second_name = name_parts[1]
            third_name = name_parts[2]
            fourth_name = name_parts[3]
            
        if not employee.work_email:
            return {'error': 'Not found'}
        
        email = employee.work_email.strip()
        if not email:
            return {'error': 'Not found'}
        
        # search for employee by email in AD
        # Get Azure AD Token
        try:
            ad_user = False
            
            # Check if user exists in Odoo and was created by Azure
            user = request.env['res.users'].sudo().search([
                ('login', '=', email),
                ('created_by_azure', '=', True),
            ], limit=1)
            if not user:
                token = self._get_azure_ad_token()
                if not token:
                    return {'error': 'AD auth failed'}
            
                ad_user = self._get_ad_user_by_email(token, email)
                _logger.info(ad_user)
                if not ad_user:
                    return {'error': 'Not found in AD'}

            return {
                'name': first_name,
                'second_name': second_name,
                'third_name': third_name,
                'fourth_name': fourth_name,

                'work_email': employee.work_email,
                'mobile_phone': employee.mobile_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '') if employee.mobile_phone else '',
                'work_phone': employee.work_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '') if employee.work_phone else '',
                'identification_id': employee.identification_id or '',
                'passport_id': employee.passport_id or '',
            }
        except Exception as e:
            _logger.error(f"Error getting employee info: {str(e)}")
            return {'error': 'AD auth failed'}
    
    @http.route('/frontdesk/get_all_employees', type='json', auth='public', csrf=False)
    def get_all_employees(self):
        """Get all employees for selection dropdown"""
        try:
            employees = request.env['hr.employee'].sudo().search([
                ('active', '=', True)
            ], order='name')
            
            employee_list = []
            for emp in employees:
                employee_list.append({
                    'id': emp.id,
                    'name': emp.name,
                    'department': emp.department_id.name if emp.department_id else '',
                    'work_email': emp.work_email or ''
                })
            
            return {'employees': employee_list}
        except Exception as e:
            _logger.error(f"Error getting all employees: {str(e)}")
            return {'employees': []}
    
    @http.route('/frontdesk/group-reservations/<int:record_id>', type='http', auth='public', website=True)
    def download_group_reservations_attachment(self, record_id):
        if not record_id:
            return request.not_found()
        
        record = request.env['frontdesk.frontdesk'].sudo().browse(record_id)
        if not record or not record.group_reservations_attachment_id:
            return request.not_found()

        file_content = base64.b64decode(record.group_reservations_attachment_id)
        filename = 'Group Reservations.xlsx'

        return request.make_response(file_content,
            headers=[('Content-Type', 'application/octet-stream'),
                     ('Content-Disposition', f'attachment; filename="{filename}"')])
    
    def _verify_token(self, frontdesk, token):
        try:
            # Check if the token matches the access token
            if consteq(frontdesk.access_token, token):
                return True
            
            # Try to parse the timestamp from the token
            # token_time_str = token[-19:]
            # token_time = fields.Datetime.from_string(token_time_str)
            # _logger.info(f"Token time: {token_time}")
            
            # # Calculate the time difference
            # time_difference = fields.Datetime.now() - token_time

            # # Check if the token is within the valid timeframe and matches the temp code
            # if time_difference.total_seconds() <= 3600 and consteq(frontdesk._get_tmp_code(), token[:64]):
            #     return True
            
        except ValueError as e:
            _logger.error(f"Token verification failed: {str(e)}")

        # return True for now
        return True

    @http.route('/kiosk/<int:frontdesk_id>/<string:token>', type='http', auth='public', website=True, csrf=False)
    def launch_frontdesk(self, frontdesk_id, token, lang='en_US'):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.exists() or not self._verify_token(frontdesk, token):
            return request.not_found()
        return self._get_additional_info(frontdesk, lang)

    @http.route('/kiosk/<int:frontdesk_id>/mobile/<string:token>', type='http', auth='public', website=True, csrf=False)
    def launch_frontdesk_mobile(self, frontdesk_id, token, lang='en_US'):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.exists() or not self._verify_token(frontdesk, token):
            return request.render('frontdesk.frontdesk_qr_expired')
        return self._get_additional_info(frontdesk, lang, is_mobile=True)

    @http.route('/kiosk/<int:frontdesk_id>/get_tmp_code/<string:token>', type='json', auth='public', csrf=False)
    def get_tmp_code(self, frontdesk_id, token):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.exists() or not self._verify_token(frontdesk, token):
            return request.not_found()
        return (frontdesk._get_tmp_code(), fields.Datetime.to_string(fields.Datetime.now()))
    
    @http.route('/frontdesk/get_recaptcha', type='json', auth='public', csrf=False)
    def get_recaptcha(self):
        try:
            site_key = request.env['ir.config_parameter'].sudo().get_param('frontdesk.recaptcha_site_key')
        except Exception as e:
            site_key = ""

        return site_key

    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/<string:lang>/get_frontdesk_data', type='json', auth='public')
    def get_frontdesk_data(self, frontdesk_id, token, lang=None):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.exists() or not self._verify_token(frontdesk, token):
            return request.not_found()
        if lang and lang != 'null':
            frontdesk = frontdesk.with_context(lang=lang)
        return frontdesk._get_frontdesk_data()

    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/get_planned_visitors', type='json', auth='public')
    def get_planned_visitors(self, frontdesk_id, token):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.exists() or not self._verify_token(frontdesk, token):
            return request.not_found()
        return frontdesk._get_planned_visitors()

    @http.route('/frontdesk/<int:frontdesk_id>/background', type='http', auth='public')
    def frontdesk_background_image(self, frontdesk_id):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.image:
            return ""
        return request.env['ir.binary']._get_image_stream_from(frontdesk, 'image').get_response()
    
    @http.route('/frontdesk/<int:frontdesk_id>/register_background', type='http', auth='public')
    def frontdesk_background_register_image(self, frontdesk_id):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.register_image:
            return ""
        return request.env['ir.binary']._get_image_stream_from(frontdesk, 'register_image').get_response()

    @http.route('/frontdesk/<int:drink_id>/get_frontdesk_drinks', type='http', auth='public')
    def get_frontdesk_drinks(self, drink_id):
        drink = request.env['frontdesk.drink'].sudo().browse(drink_id)
        return request.env['ir.binary']._get_image_stream_from(drink, 'drink_image').get_response()

    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/<string:lang>/get_hosts', type='json', auth='public', csrf=False)
    def get_hosts(self, frontdesk_id, token, name, purpose_id=None, lang=None):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.exists() or not self._verify_token(frontdesk, token):
            return request.not_found()
        dept_obj = request.env['hr.department']
        if lang and lang != 'null':
            dept_obj = dept_obj.with_context(lang=lang)

        domain = [('company_id', '=', frontdesk.company_id.id)]
        # Filter by department_ids if provided
        if purpose_id:
            _logger.info('get_hosts: purpose_id')
            _logger.info(purpose_id)
            purpose = request.env['frontdesk.visit.purpose'].sudo().browse(purpose_id)
            if purpose.exists():
                domain.append(('id', 'in', purpose.department_ids.ids))

        dept_data = dept_obj.sudo().name_search(name, domain)
        return dept_data
    
    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/<string:lang>/get_purposes', type='json', auth='public', csrf=False)
    def get_purposes(self, frontdesk_id, token, name, lang=None):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.exists() or not self._verify_token(frontdesk, token):
            return request.not_found()
        
        purpose_obj = request.env['frontdesk.visit.purpose']
        if lang and lang != 'null':
            purpose_obj = purpose_obj.with_context(lang=lang)
        
        # Only fetch filtered purposes
        purpose_ids = purpose_obj.sudo().name_search(name, [])
        if not purpose_ids:
            return []

        filtered_purposes = purpose_obj.sudo().browse([p[0] for p in purpose_ids])
        
        # Fetch is_other field
        purposes_data = [
            (purpose.id, purpose.name, purpose.is_other, purpose.state_ids)
            for purpose in filtered_purposes
        ]

        return purposes_data
    
    @http.route('/frontdesk/get_other_reasons', type='json', auth='public', csrf=False)
    def get_other_reasons(self):
        other_reasons = request.env['frontdesk.other.reason'].sudo().search([])
        return [
            {'id': reason.id, 'name': reason.name}
            for reason in other_reasons
        ]
    
    @http.route('/frontdesk/get_wilayat', type='json', auth='public', csrf=False)
    def get_wilayat(self, purpose_id=None):
        _logger.info('get_wilayat')
        _logger.info(purpose_id)
        if purpose_id:
            purpose = request.env['frontdesk.visit.purpose'].sudo().browse(purpose_id)
            return [
                {'id': state_id.id, 'name': state_id.name}
                for state_id in purpose.state_ids
            ]
        return []
    
    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/get_holidays', type='json', auth='public', csrf=False)
    def get_holidays(self, frontdesk_id, token):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.exists() or not self._verify_token(frontdesk, token):
            return request.not_found()
        holidays_obj = request.env['frontdesk.holiday']

        holidays_data = holidays_obj.sudo().search_read([], ['date_from', 'date_to'])
        return holidays_data

    @http.route('/frontdesk/validate_recaptcha', type='json', auth='public', csrf=False)
    def validate_recaptcha(self, recaptcha_response):
        """
        Validate the Google reCAPTCHA response token.
        """
        try:
            # Fetch the reCAPTCHA secret key from system parameters
            recaptcha_secret = request.env['ir.config_parameter'].sudo().get_param('frontdesk.recaptcha_secret_key')
            
            if not recaptcha_secret or recaptcha_secret == 'False' or recaptcha_secret == 'None' or recaptcha_secret == 'null' or recaptcha_secret == 'undefined' or recaptcha_secret == '':
                recaptcha_secret = '6LfQy7QqAAAAAJJ8mf10okZO1pmtzmpnoU-G1EYJ'

            # Verify the reCAPTCHA response with Google's API
            recaptcha_verify_url = 'https://www.google.com/recaptcha/api/siteverify'
            data = {
                'secret': recaptcha_secret,
                'response': recaptcha_response,
            }
            verification_response = requests.post(recaptcha_verify_url, data=data)
            verification_result = verification_response.json()
            _logger.info("reCAPTCHA verification result: %s", verification_result)

            # Check if the verification was successful
            if verification_result.get('success'):
                return {'success': True}
            else:
                return {'success': False, 'message': verification_result.get('error-codes', 'Unknown error')}
        except Exception as e:
            _logger.error("Error during reCAPTCHA verification: %s", str(e))
            return {'success': False, 'message': 'An error occurred while verifying reCAPTCHA.'}
    
    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/<string:lang>/get_employees', type='json', auth='public', csrf=False)
    def get_employees(self, frontdesk_id, token, name, purpose_id=None, lang=None):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.exists() or not self._verify_token(frontdesk, token):
            return request.not_found()
        
        employee_obj = request.env['hr.employee']
        if lang and lang != 'null':
            employee_obj = employee_obj.with_context(lang=lang)

        domain = [('company_id', '=', frontdesk.company_id.id)]
        
        # Filter by purpose_id if provided
        if purpose_id:
            _logger.info('get_employees: purpose_id')
            _logger.info(purpose_id)
            purpose = request.env['frontdesk.visit.purpose'].sudo().browse(int(purpose_id))
            if purpose.exists() and purpose.department_ids:
                domain.append(('department_id', 'in', purpose.department_ids.ids))

        # Search employees by name
        employee_data = employee_obj.sudo().name_search(name, domain)
        
        # Enhance the data with additional fields
        enhanced_data = []
        for emp_data in employee_data:
            employee = employee_obj.sudo().browse(emp_data[0])
            enhanced_data.append([
                emp_data[0],  # ID
                emp_data[1],  # Display name
                employee.work_email or '',  # Work email
                employee.mobile_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '') if employee.mobile_phone else '',  # Mobile phone
                employee.work_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '') if employee.work_phone else '',  # Work phone
            ])
        
        return enhanced_data
    
    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/prepare_visitor_data', type='json', auth='public', methods=['POST'])
    def prepare_visitor_data(self, frontdesk_id, token, visitor_id=None, **kwargs):
        frontdesk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
        if not frontdesk.exists() or not self._verify_token(frontdesk, token):
            return request.not_found()
        _logger.info('prepare_visitor_data')
        _logger.info(kwargs.get('visitor_card'))
        _logger.info('kwargs')
        _logger.info(kwargs)
        _logger.info('is_online')
        _logger.info(frontdesk.is_online)

        # check if recaptcha response is valid
        try:
            if frontdesk.allow_recaptcha:
                recaptcha_response = kwargs.get('recaptcha_response')
                recaptcha_verify_url = 'https://www.google.com/recaptcha/api/siteverify'
                recaptcha_secret = request.env['ir.config_parameter'].sudo().get_param('frontdesk.recaptcha_secret_key')
                if not recaptcha_secret or recaptcha_secret == 'False' or recaptcha_secret == 'None' or recaptcha_secret == 'null' or recaptcha_secret == 'undefined' or recaptcha_secret == '':
                    recaptcha_secret = '6LfQy7QqAAAAAJJ8mf10okZO1pmtzmpnoU-G1EYJ'

                data = {'secret': recaptcha_secret, 'response': recaptcha_response}
                _logger.info('data')
                _logger.info(data)

                recaptcha_verification = requests.post(recaptcha_verify_url, data=data).json()
                _logger.info('recaptcha_verification')
                _logger.info(recaptcha_verification)
                if not recaptcha_verification.get('success'):
                    _logger.error(f"reCAPTCHA {recaptcha_secret} verification failed: {recaptcha_verification}")
                    _logger.error(f"reCAPTCHA response: {recaptcha_response}")
                    error_values = {
                            'error': True,
                            'status': False,
                            'message': 'reCAPTCHA verification failed. Please try again.',
                        }
                    return error_values
        except Exception as e:
            _logger.error(f"Error verifying reCAPTCHA: {str(e)}")

        department = kwargs.get('host_ids', [])
        host_name = kwargs.get('host_name', [])
        host_phone = kwargs.get('host_phone', [])
        host_email = kwargs.get('host_email', [])
        is_recurring = True if 'is_recurring' in kwargs and kwargs.get('is_recurring') == 'on' else False
        planned_date = kwargs.get('planned_date')
        planned_date_end = kwargs.get('planned_date_end') if 'planned_date_end' in kwargs and 'is_recurring' in kwargs and kwargs.get('is_recurring') == 'on' else False
        planned_time = kwargs.get('planned_time')
        planned_duration = kwargs.get('planned_duration')
        visit_purpose = kwargs.get('visit_purpose')
        other_reason = kwargs.get('other_reason') if 'other_reason' in kwargs else False
        emp_id = kwargs.get('emp_id')
        other_reason_id = False

        if other_reason:
            try:
                other_reason_obj = request.env['frontdesk.other.reason'].sudo().browse(int(other_reason))
                if other_reason_obj.exists():
                    other_reason_id = other_reason_obj.id
            except Exception as e:
                _logger.error(f"Error fetching other reason: {str(e)}")

        # if host_email and host_email does not contain '@', then add the domain
        if not frontdesk.is_online and host_email and '@' not in host_email and host_email[0]:
            host_email[0] = host_email[0] + frontdesk.email_host_domain
        # Convert planned_time from 'HH:MM' to float
        planned_time_float = None
        _logger.info('kwargs')
        _logger.info(kwargs)
        
        # if planned_time is 0 or None, set it to default value 09:00
        if not planned_time or planned_time == '0' or planned_time == '00:00':
            planned_time = '09:00'
            
        if planned_time:
            hours, minutes = map(int, planned_time.split(':'))
            planned_time_float = hours + minutes / 60.0

        email =  kwargs.get('email') if kwargs.get('email') else False
        phone = kwargs.get('phone') if kwargs.get('phone') else False
        if not email and not phone and emp_id:
            employee = request.env['hr.employee'].sudo().search([('barcode', '=', str(emp_id))], limit=1)
            if employee:
                email = employee.work_email
                phone = employee.mobile_phone

        new_department = False
        new_department_id = department[0] if department else False
        if new_department_id:
            try:
                new_department = request.env['hr.department'].sudo().browse(new_department_id)
                if new_department:
                    new_department = new_department.id
            except Exception as e:
                _logger.error(f"Error fetching department: {str(e)}")
                new_department = False
                
        # if planned_duration is None or planned_duration == '0' or planned_duration == '00':
        if not planned_duration:
            planned_duration = 30

        vals = {
            'station_id': frontdesk.id,
            'name': kwargs.get('name'),
            'second_name': kwargs.get('second_name'),
            'third_name': kwargs.get('third_name'),
            'fourth_name': kwargs.get('fourth_name'),
            'phone': phone,
            'landline': kwargs.get('landline'),
            'email': email,
            'company': kwargs.get('company'),
            'date': fields.Date.today(),
            'department_id': new_department,
            'employee_name': host_name[0] if host_name else False,
            'employee_phone': host_phone[0] if host_phone else False,
            'employee_email': host_email[0] if host_email else False,
            'host_landline': str(kwargs.get('host_landline')) if 'host_landline' in kwargs else '',
            'is_recurring': is_recurring if is_recurring else False,
            'planned_date': planned_date if planned_date else fields.Date.today(),
            'planned_date_end': planned_date_end if planned_date_end else fields.Date.today(),
            'planned_time': planned_time_float,
            'planned_duration': float(planned_duration) if planned_duration else None,
            'visitor_id_number': kwargs.get('visitor_card'),
            'passport': kwargs.get('passport'),
            'visit_purpose': visit_purpose or 'other',
            'source': kwargs.get('source') if 'source' in kwargs else 'in_person',
            'emp_id': emp_id or False,
            'visit_type': kwargs.get('visit_type') if 'visit_type' in kwargs else False,
            'wilayat_id': kwargs.get('wilayat') if frontdesk.is_online and 'wilayat' in kwargs else False,
            'is_online': frontdesk.is_online,
            'preferred_language': kwargs.get('preferred_language') if 'preferred_language' in kwargs else 'en_US',
        }
        _logger.info('prepare_visitor_data')

        _logger.info(is_recurring)
        _logger.info(planned_date_end)
        if kwargs.get('visit_type') == 'employee':
            vals['department_id'] = False
            if new_department:
                vals['department_id'] = new_department

        _logger.info('vals new')
        _logger.info(vals)
        visitor = request.env['frontdesk.request'].sudo().create(vals)
        if visitor and other_reason_id:
            visitor.write({'other_reason_id': other_reason_id})
        if frontdesk and frontdesk.is_online and visitor:
            visitor.write({'source': 'online'})


        try:
            if visitor and not visitor.visitor_id:
                visitor.action_create_visitor()
        except Exception as e:
            _logger.error(f"Error creating visitor (action_create_visitor): {str(e)}")

        try:
            if frontdesk and not visitor.employee_id and frontdesk.security_employee_id:
                security_employee_id = frontdesk.security_employee_id
                if security_employee_id:
                    visitor.write({'employee_id': security_employee_id.id})
        except Exception as e:
            _logger.error(f"Change employee error: {str(e)}")
            
        try:
            if visitor and visitor.employee_id:
                visitor.write({'employee_email': visitor.employee_id.work_email or visitor.employee_email})
                visitor.send_email_to_host()
        except Exception as e:
            _logger.error(f"Error sending email to host (send_email_to_host): {str(e)}")
            
        return {'visitor_id': visitor.id}

    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/frontdesk_check_in', type='json', auth='public',
                methods=['POST'])
    def frontdesk_check_in(self, frontdesk_id, token, **kwargs):
        try:
            qr_code = kwargs.get('qrCode')
            visitor = request.env['frontdesk.visitor'].sudo().search([('qr_string', '=', qr_code)], limit=1)
            if not visitor:
                _logger.info('frontdesk_check_in: visitor not found')
                return {'message': 'Invalid QR Code!'}
            kiosk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
            if not kiosk:
                _logger.info('frontdesk_check_in: kiosk not found')
                return {'message': 'Something went wrong!'}
            
            if not kiosk.operating_unit_id or not visitor.operating_unit_id or (kiosk.operating_unit_id and visitor.operating_unit_id and kiosk.operating_unit_id.id != visitor.operating_unit_id.id):
                _logger.info('frontdesk_check_in: operating unit not matched')
                return {'success': False, 'message': 'You are not allowed to check in from this kiosk!'}
            
            if visitor and visitor.state not in ['checked_in', 'checked_out', 'canceled', 'absent']:
                # Convert planned_time (float) to a proper time object
                try:
                    if visitor.planned_time is not None:
                        planned_hour = int(visitor.planned_time)
                        planned_minute = int((visitor.planned_time % 1) * 60)
                        planned_check_in_time = time(planned_hour, planned_minute)
                    else:
                        planned_check_in_time = None  # No planned time
                    _logger.info(f"Planned check-in time: {planned_check_in_time}")

                    # Get current date and time
                    muscat_tz = timezone('Asia/Muscat')
                    current_datetime = datetime.now(muscat_tz)
                    current_date = current_datetime.date()
                    current_time = current_datetime.time()
                    _logger.info(f"Current time: {current_time}")
                    _logger.info(f"Current date: {current_date}")

                except Exception as e:
                    _logger.error(f"Error converting planned time: {str(e)}")
                    return {'message': 'The check-in time is invalid'}
                if visitor.date:
                    if visitor.date != current_date:
                        return {'success': False, 'message': f'Your visit is scheduled for {visitor.date.strftime("%d-%m-%Y")}'}
                    planned_datetime = datetime.combine(visitor.date, planned_check_in_time) if planned_check_in_time else None
                    _logger.info(f"Planned check-in datetime: {planned_datetime}")
                    if planned_datetime:
                        allowed_start_time = (planned_datetime - timedelta(minutes=30)).time()  # 30 min before
                        allowed_end_time = (planned_datetime + timedelta(minutes=30)).time()    # 30 min after
                        if not (allowed_start_time <= current_time <= allowed_end_time):
                            return {'success': False, 'message': f'Your visit is scheduled between {allowed_start_time.strftime("%H:%M")} and {allowed_end_time.strftime("%H:%M")}.'}
                    
                    _logger.info('frontdesk_check_in: checking in')
                    visitor.action_check_in()
                    return {'message': 'Successfully Checked In'}
                else:
                    _logger.info('frontdesk_check_in: invalid date')
                    return {'message': 'Invalid QR Code, please try again'}
                
            return {'message': 'Invalid QR Code, please try again'}
        except Exception as e:
            _logger.error(f"Error checking in visitor: {str(e)}")
            return {'message': 'Invalid QR Code!'}
    
    # cancel visit
    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/frontdesk_cancel_visit', type='json', auth='public',
                methods=['POST'])
    def frontdesk_cancel_visit(self, frontdesk_id, token, **kwargs):
        qr_code = kwargs.get('qrCode')
        reason = kwargs.get('reason')
        visitor = request.env['frontdesk.visitor'].sudo().search([('qr_string', '=', qr_code)], limit=1)
        if visitor:
            visitor.action_canceled()
            visitor.write({'cancel_reason': reason})
            return {'message': 'Successfully Cancelled!'}
        return {'message': 'Invalid QR Code!'}
    
    # extend visit
    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/frontdesk_extend_visit', type='json', auth='public',
                methods=['POST'])
    def frontdesk_extend_visit(self, frontdesk_id, token, **kwargs):
        qr_code = kwargs.get('qrCode')
        visitor = request.env['frontdesk.visitor'].sudo().search([('qr_string', '=', qr_code)], limit=1)
        if visitor:
            visitor.action_request_extend_visit()
            return {
                'id': visitor.id,
                'success': True,
                'planned_duration': visitor.planned_duration,
                'message': 'Successfully Extended!'
                }
        return {
                'success': False,
                'message': 'Invalid QR Code!'
                }
    
    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/update_extension', type='json', auth='public', methods=['POST'])
    def update_extension(self, frontdesk_id, token, **kwargs):
        visitor_id = kwargs.get('visitor_id')
        extension = kwargs.get('extension')
        visitor = request.env['frontdesk.visitor'].sudo().browse(visitor_id)
        if visitor:
            visitor.action_extend_visit(extension)
            return {
                'success': True,
                'message': 'Visit extension requested!'
            }
        return {
            'success': False,
            'message': 'Invalid Data!'
        }
    
    # check out
    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/frontdesk_check_out', type='json', auth='public',
                methods=['POST'])
    def frontdesk_check_out(self, frontdesk_id, token, **kwargs):
        try:
            qr_code = kwargs.get('qrCode')
            visitor = request.env['frontdesk.visitor'].sudo().search([('qr_string', '=', qr_code)], limit=1)
            kiosk = request.env['frontdesk.frontdesk'].sudo().browse(frontdesk_id)
            if not kiosk:
                _logger.info('frontdesk_check_out: kiosk not found')
                return {'success': False, 'message': 'Something went wrong!'}
            
            # if the visit is not online:
            if not visitor:
                _logger.info('frontdesk_check_out: visitor not found')
                return {'success': False, 'message': 'Something went wrong!'}

            if not kiosk.operating_unit_id or not visitor.operating_unit_id or (kiosk.operating_unit_id and visitor.operating_unit_id and kiosk.operating_unit_id.id != visitor.operating_unit_id.id):
                _logger.info('frontdesk_check_out: operating unit not matched')
                return {'success': False, 'message': 'You are not allowed to check out from this kiosk!'}

            if visitor and visitor.state not in ['checked_out', 'canceled', 'absent']:
                _logger.info('frontdesk_check_out: checking out')
                visitor.action_check_out()
                nfc_card_number = visitor.nfc_card_number
                visitor_id = visitor.id
                visitor_name = visitor.partner_id.name if visitor.partner_id else ''
                return {
                    'success': True,
                    'message': 'Successfully Checked Out!',
                    'nfc_card_number': nfc_card_number,
                    'visitor_id': visitor_id,
                    'visitor_name': visitor_name
                    }
            return {
                'success': False,
                'message': 'Invalid QR Code!'
                }
        except Exception as e:
            _logger.error(f"Error checking out visitor: {str(e)}")
            return {'success': False, 'message': 'Invalid QR Code!'}
    
    @http.route('/frontdesk/<int:frontdesk_id>/<string:token>/submit_evaluation', type='json', auth='public', methods=['POST'])
    def submit_evaluation(self, frontdesk_id, token, **kwargs):
        qr_code = kwargs.get('qrCode')
        evaluation = kwargs.get('evaluation')
        comment = kwargs.get('comment')
        visitor = request.env['frontdesk.visitor'].sudo().search([('qr_string', '=', qr_code)], limit=1)
        if visitor:
            visitor.evaluation = evaluation
            visitor.evaluation_comment = comment
            visitor.state = 'checked_out'
            return {'success': True}
        return {'error': 'Visitor not found'}
    
    
    @http.route('/frontdesk/approve_visitor/<int:visitor_id>', type='http', auth='user', website=True, csrf=False)
    def approve_visitor(self, visitor_id):
        visitor = request.env['frontdesk.request'].sudo().browse(visitor_id)
        if visitor and visitor.state in ['draft']:
            visitor.action_approve()
            return request.render('frontdesk.thank_you_page', {'message': 'Thank you! The visitor has been approved.'})
        return request.render('frontdesk.thank_you_page', {'message': 'This request is invalid or has already been processed.'})
    
    @http.route('/frontdesk/finish_visit/<int:visitor_id>', type='http', auth='user', website=True, csrf=False)
    def finish_visit(self, visitor_id):
        visitor = request.env['frontdesk.request'].sudo().browse(visitor_id)
        if visitor and visitor.request_visit_id:
            visitor.request_visit_id.action_finish()
            return request.render('frontdesk.thank_you_page', {'message': 'Thank you! The visit has been finished.'})
        return request.render('frontdesk.thank_you_page', {'message': 'This request is invalid or has already been processed.'})

    @http.route('/frontdesk/reject_visitor/<int:visitor_id>', type='http', auth='user', website=True, csrf=False)
    def reject_visitor(self, visitor_id, **post):
        visitor = request.env['frontdesk.request'].sudo().browse(visitor_id)
        # if visitor and visitor.state in ['draft']:
        #     visitor.action_reject_portal()
        #     return request.render('frontdesk.thank_you_page', {'message': 'Thank you! The visitor has been rejected.'})
        # return request.render('frontdesk.thank_you_page', {'message': 'This request is invalid or has already been processed.'})
        # If the request method is POST, user clicked "Submit"

        # check if the user is logged in and is internal user
        if not visitor or not request.env.user or not request.env.user.has_group('base.group_user'):
            return request.render('frontdesk.thank_you_page', {
                'message': 'You are not authorized to perform this action.'
            })
        
        try:
            if request.httprequest.method == 'POST':
                _logger.info('reject_visitor post request')
                selected_reason_id = post.get('reason_id')
                _logger.info(selected_reason_id)
                _logger.info(visitor)

                if visitor and visitor.state in ['draft']:
                    reject_reason_id = False
                    if selected_reason_id:
                        reject_reason_id = int(selected_reason_id)
                    visitor.action_reject_portal(reject_reason_id)
                    return request.render('frontdesk.thank_you_page', {
                        'message': 'Thank you! The visitor has been rejected.'
                    })

                # If invalid or processed
                return request.render('frontdesk.thank_you_page', {
                    'message': 'This request is invalid or has already been processed.'
                })
            else:
                # Otherwise, it's a GET => Display the rejection form
                if not visitor or visitor.state not in ['draft']:
                    return request.render('frontdesk.thank_you_page', {
                        'message': 'This request is invalid or has already been processed.'
                    })

                # Prepare the list of possible rejection reasons
                reasons = request.env['visit.reject.reason'].sudo().search([])
                return request.render('frontdesk.reject_visitor_form', {
                    'visitor': visitor,
                    'reasons': reasons,
                })
        except Exception as e:
            _logger.error(f"Error rejecting visitor: {str(e)}")
            return request.render('frontdesk.thank_you_page', {
                'message': 'An error occurred while processing your request.'
            })
    @http.route('/frontdesk/submit_group_reservation', type='json', auth='public', csrf=False, save_session=False)
    def submit_group_reservation(self, **kwargs):
        """Handle group reservation submission"""
        try:
            company_name = kwargs.get('company_name')
            hosting_employee_id = kwargs.get('hosting_employee_id')
            visit_date = kwargs.get('visit_date')
            visit_time = kwargs.get('visit_time')
            visitors = kwargs.get('visitors', [])
            station_id = kwargs.get('station_id')
            
            if not all([company_name, hosting_employee_id, visit_date, visit_time, visitors, station_id]):
                return {'success': False, 'error': 'Missing required fields'}
                
            # Get the hosting employee
            hosting_employee = request.env['hr.employee'].sudo().browse(hosting_employee_id)
            if not hosting_employee.exists():
                return {'success': False, 'error': 'Invalid hosting employee'}
            
            # Parse visit datetime
            visit_datetime = datetime.strptime(f"{visit_date} {visit_time}", '%Y-%m-%d %H:%M')
            
            # Convert time to float (hours)
            planned_time = visit_datetime.hour + visit_datetime.minute / 60.0
            
            # Find or create company
            company = request.env['res.partner'].sudo().search([
                ('name', '=', company_name),
                ('is_company', '=', True),
                ('is_visitor', '=', True)
            ], limit=1)
            
            if not company:
                company = request.env['res.partner'].sudo().create({
                    'name': company_name,
                    'is_company': True,
                    'is_visitor': True
                })
            
            # hosting_employee is already loaded above as the record
            
            # Generate a unique group reference for linking requests
            from datetime import datetime
            group_reference = f"GRP-{visit_date.replace('-', '')}-{datetime.now().strftime('%H%M%S')}-{len(visitors)}"
            
            created_requests = []
            
            # Process each visitor
            for visitor_data in visitors:
                # Find or create visitor partner
                visitor_partner = request.env['res.partner'].sudo().search([
                    ('national_id', '=', visitor_data['id_number'])
                ], limit=1)
                
                if not visitor_partner:
                    visitor_partner = request.env['res.partner'].sudo().create({
                        'name': visitor_data['name'],
                        'email': visitor_data['email'],
                        'phone': visitor_data['phone'],
                        'national_id': visitor_data['id_number'],
                        'is_visitor': True,
                        'parent_id': company.id
                    })
                else:
                    # Update existing partner
                    visitor_partner.write({
                        'name': visitor_data['name'],
                        'email': visitor_data['email'],
                        'phone': visitor_data['phone'],
                        'parent_id': company.id
                    })
                
                # Create visit request record (not visitor directly)
                request_vals = {
                    'name': visitor_data['name'],
                    'email': visitor_data['email'],
                    'phone': visitor_data['phone'],
                    'visitor_id': visitor_partner.id,
                    'station_id': station_id,
                    'date': visit_date,
                    'planned_time': planned_time,
                    'planned_duration': 60,  # Default 1 hour
                    'visit_purpose': f'Group visit for {company_name} [{group_reference}]',
                    'source': 'online',
                    'state': 'draft',
                    'company_id': company.id,
                }
                
                # Add host employee if found
                if hosting_employee:
                    request_vals['employee_id'] = hosting_employee.id
                
                visit_request = request.env['frontdesk.request'].sudo().create(request_vals)
                created_requests.append(visit_request)
            
            # Requests are grouped by the group_reference in their visit_purpose
            # The host employee can approve/reject them as a group or individually
            
            return {
                'success': True, 
                'message': f'Group reservation requests created successfully for {len(visitors)} visitors. Awaiting host approval.',
                'request_count': len(created_requests),
                'request_ids': [req.id for req in created_requests]
            }
            
        except Exception as e:
            _logger.error(f'Error submitting group reservation: {str(e)}')
            return {'success': False, 'error': 'Failed to submit group reservation'}

