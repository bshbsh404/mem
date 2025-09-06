# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import requests
import logging
import xml.etree.ElementTree as ET
from datetime import datetime

_logger = logging.getLogger(__name__)


class PoliceApiConfig(models.Model):
    _name = 'police.api.config'
    _description = 'ROP (Royal Oman Police) API Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Configuration Name', required=True, default='ROP API')
    
    # OAuth Settings
    auth_base_url = fields.Char(string='Auth Base URL', required=True, 
                               default='https://idcs-354938caa1a24a4189d498b4ebcb0fc0.identity.oraclecloud.com',
                               help='Oracle IDCS base URL for authentication')
    api_base_url = fields.Char(string='API Base URL', required=True,
                              default='https://IntnwsApi.nws.nama.om',
                              help='ROP API base URL')
    client_id = fields.Char(string='Client ID', required=True,
                           help='OAuth Client ID')
    client_secret = fields.Char(string='Client Secret', required=True,
                               help='OAuth Client Secret')
    scope = fields.Char(string='Scope', required=True,
                       default='IntnwsApi.nws.nama.om/VMS',
                       help='OAuth scope')
    
    # API Headers
    auth_key = fields.Char(string='Auth Key', required=True,
                          help='API auth-key header')
    consumer_code = fields.Char(string='Consumer Code', required=True,
                               default='VMS',
                               help='Consumer code for API')
    esb_category_code = fields.Char(string='ESB Category Code', required=True,
                                   default='INT',
                                   help='ESB category code')
    crn_of_request = fields.Char(string='CRN of Request', required=True,
                                help='CRN of the requesting system')
    
    # General Settings
    timeout = fields.Integer(string='Timeout (seconds)', default=30,
                           help='Request timeout in seconds')
    active = fields.Boolean(string='Active', default=True)
    
    def get_oauth_token(self):
        """
        الحصول على access token من Oracle IDCS
        """
        try:
            url = f"{self.auth_base_url}/oauth2/v1/token"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': self.scope
            }
            
            _logger.info(f"Getting OAuth token from: {url}")
            
            response = requests.post(url, headers=headers, data=data, timeout=self.timeout)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                if access_token:
                    _logger.info("OAuth token obtained successfully")
                    return access_token
                else:
                    _logger.error("No access token in response")
                    return None
            else:
                _logger.error(f"OAuth error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            _logger.error(f"OAuth token error: {str(e)}")
            return None

    def get_visitor_data(self, civil_id, card_expiry=None):
        """
        استرجاع بيانات الزائر من ROP API
        """
        if not self.active:
            raise UserError(_('ROP API configuration is not active'))
            
        if not civil_id:
            raise UserError(_('Civil ID is required'))
            
        try:
            # الحصول على access token
            access_token = self.get_oauth_token()
            if not access_token:
                return {
                    'success': False,
                    'error': _('Failed to get OAuth token')
                }
            
            # إعداد timestamp و request ID
            now = datetime.now()
            request_timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            request_id = f"VMS{now.strftime('%Y%m%d%H%M%S')}{civil_id}"
            
            # إعداد headers
            headers = {
                'Content-Type': 'application/xml',
                'Authorization': f'Bearer {access_token}',
                'auth-key': self.auth_key,
                'consumer-code': self.consumer_code,
                'esb-category-code': self.esb_category_code,
                'request-timestamp': request_timestamp,
                'request-id': request_id
            }
            
            # إعداد card_expiry (استخدم قيمة افتراضية إذا لم يتم توفيرها)
            if not card_expiry:
                card_expiry = "2030-04-29"  # قيمة افتراضية
            
            # إعداد SOAP body
            soap_body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:rop-gov-om:person">
   <soapenv:Header/>
   <soapenv:Body>
      <urn:PersonInformation>
         <PersonRequest>
            <crn>{civil_id}</crn>
            <cardExpiryDate>{card_expiry}</cardExpiryDate>
            <crnOfRequest>{self.crn_of_request}</crnOfRequest>
         </PersonRequest>
      </urn:PersonInformation>
   </soapenv:Body>
</soapenv:Envelope>"""
            
            # إرسال الطلب
            url = f"{self.api_base_url}/api/getpersoninformation"
            _logger.info(f"Calling ROP API: {url} for Civil ID: {civil_id}")
            
            response = requests.post(url, headers=headers, data=soap_body, timeout=self.timeout)
            
            # معالجة الاستجابة
            if response.status_code == 200:
                return self._parse_rop_response(response.text, civil_id)
            else:
                _logger.error(f"ROP API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': _('Failed to retrieve data from ROP API')
                }
                
        except requests.RequestException as e:
            _logger.error(f"ROP API connection error: {str(e)}")
            return {
                'success': False,
                'error': _('Connection error with ROP API')
            }
        except Exception as e:
            _logger.error(f"Unexpected error in ROP API call: {str(e)}")
            return {
                'success': False,
                'error': _('Unexpected error occurred')
            }

    def _parse_rop_response(self, xml_response, civil_id):
        """
        تحليل استجابة XML من ROP API
        """
        try:
            _logger.info(f"Parsing ROP response for Civil ID: {civil_id}")
            
            # تنظيف XML وإزالة namespaces
            cleaned_xml = xml_response.replace('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
            cleaned_xml = cleaned_xml.replace('xsi:nil="true"', '')
            
            root = ET.fromstring(cleaned_xml)
            
            # البحث عن Person element
            person = root.find('.//Person')
            if person is None:
                return {
                    'success': False,
                    'error': _('No person data found in response')
                }
            
            # استخراج الأسماء
            name_element = person.find('.//Name')
            name_1_ar = self._get_xml_text(name_element, 'name_1_ar')
            name_2_ar = self._get_xml_text(name_element, 'name_2_ar')
            name_3_ar = self._get_xml_text(name_element, 'name_3_ar')
            name_4_ar = self._get_xml_text(name_element, 'name_4_ar')
            
            # استخراج رقم الهاتف
            mobile_number = self._get_xml_text(person, './/mobileNumber')
            
            # استخراج تاريخ الميلاد
            birth_date = self._get_xml_text(person, './/dateOfBirth')
            
            # إعداد البيانات المُستخرجة
            data = {
                'name': name_1_ar or '',
                'second_name': name_2_ar or '',
                'third_name': name_3_ar or '',
                'fourth_name': name_4_ar or '',
                'phone': mobile_number or '',
                'email': '',  # لا يتوفر في API الشرطة
                'civil_id': civil_id,
                'birth_date': birth_date or '',
                'address': '',  # يمكن إضافته لاحقاً من عنصر Address
            }
            
            _logger.info(f"Successfully parsed ROP data: {data}")
            
            return {
                'success': True,
                'data': data
            }
            
        except ET.ParseError as e:
            _logger.error(f"XML parsing error: {str(e)}")
            return {
                'success': False,
                'error': _('Invalid XML response from ROP API')
            }
        except Exception as e:
            _logger.error(f"Error parsing ROP response: {str(e)}")
            return {
                'success': False,
                'error': _('Error processing ROP API response')
            }

    def _get_xml_text(self, parent, xpath):
        """
        استخراج نص من XML element مع معالجة الأخطاء
        """
        try:
            if parent is None:
                return None
            element = parent.find(xpath)
            if element is not None and element.text:
                return element.text.strip()
            return None
        except Exception:
            return None

    @api.model
    def get_active_config(self):
        """الحصول على الإعداد النشط"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            raise UserError(_('No active Police API configuration found'))
        return config