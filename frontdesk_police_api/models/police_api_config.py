# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import requests
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

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
                              default='https://IntnwsApi.nws.nama.om/api/getpersoninformation',
                              help='ROP API base URL')
    client_id = fields.Char(string='Client ID', required=True,
                           default='cf70c538b29f4bee993b6cd0bfc36856',
                           help='OAuth Client ID')
    client_secret = fields.Char(string='Client Secret', required=True,
                               default='idcscs-36bada7d-b6a3-4806-ad81-7c23b93d89cf',
                               help='OAuth Client Secret')
    scope = fields.Char(string='Scope', required=True,
                       default='IntnwsApi.nws.nama.om/VMS',
                       help='OAuth scope')
    
    # API Headers
    auth_key = fields.Char(string='Auth Key', required=True,
                          default='zQ84RpT1xGnECMvf92bKLUYt6mJdoAWX',
                          help='API auth-key header')
    consumer_code = fields.Char(string='Consumer Code', required=True,
                               default='VMS',
                               help='Consumer code for API')
    esb_category_code = fields.Char(string='ESB Category Code', required=True,
                                   default='INT',
                                   help='ESB category code')
    crn_of_request = fields.Char(string='CRN of Request', required=True,
                                default='6022158',
                                help='CRN of the requesting system (fixed value = 6022158)')
    
    # General Settings
    timeout = fields.Integer(string='Timeout (seconds)', default=60,
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

    def get_visitor_data(self, civil_id, card_expiry=None, context=None):
        """
        استرجاع بيانات الزائر من ROP API
        """
        if not self.active:
            raise UserError(_('ROP API configuration is not active'))
            
        if not civil_id:
            raise UserError(_('Civil ID is required'))
            
        try:
            # تسجيل مفصل للتحليل
            debug_file = '/tmp/rop_api_debug.log'
            with open(debug_file, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"ROP API DEBUG LOG - {datetime.now()}\n")
                f.write(f"Civil ID: {civil_id}\n")
                f.write(f"Card Expiry (input): {card_expiry}\n")
                
            # الحصول على access token
            access_token = self.get_oauth_token()
            if not access_token:
                return {
                    'success': False,
                    'error': _('Failed to get OAuth token')
                }
            _logger.info(f"OAuth token obtained (length: {len(access_token)}): {access_token[:50]}...")
            
            with open(debug_file, 'a') as f:
                f.write(f"OAuth Token Length: {len(access_token)}\n")
            
            # إعداد timestamp و request ID مطابق للوثائق الرسمية NWS
            import random
            # توقيت عمان (+4 ساعات من UTC)
            oman_tz = timezone(timedelta(hours=4))
            now = datetime.now(oman_tz)
            # تنسيق مطابق للوثائق الرسمية: YYYY-MM-DD HH:MM:SS, 24-Hour Format
            request_timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            # Request ID: First 4 characters of Vendor Code + Random Numeric String (max 36 characters)
            random_number = str(random.randint(100000000, 999999999))  # 9-digit random number
            request_id = f"VMS{random_number}"
            
            _logger.info(f"Request timestamp: {request_timestamp}")
            _logger.info(f"Request ID: {request_id}")
            
            # إعداد headers مطابق لـ Postman الناجح
            headers = {
                'Content-Type': 'application/xml',
                'Authorization': f'Bearer {access_token}',
                'auth-key': self.auth_key,
                'consumer-code': self.consumer_code,
                'esb-category-code': self.esb_category_code,
                'request-timestamp': request_timestamp,
                'request-id': request_id,
                'Accept': 'application/xml',
                'Cache-Control': 'no-cache'
            }
            
            _logger.info(f"Request headers: {headers}")
            
            with open(debug_file, 'a') as f:
                f.write(f"Request Timestamp: {request_timestamp}\n")
                f.write(f"Request Headers: {headers}\n")
            
            # إعداد card_expiry وتحويل التنسيق إلى YYYY-MM-DD
            original_card_expiry = card_expiry
            if not card_expiry:
                card_expiry = "2030-04-29"  # قيمة افتراضية بتنسيق YYYY-MM-DD
            else:
                # تحويل التنسيق إلى YYYY-MM-DD
                try:
                    if '/' in card_expiry:
                        # من MM/DD/YYYY إلى YYYY-MM-DD
                        date_obj = datetime.strptime(card_expiry, '%m/%d/%Y')
                        card_expiry = date_obj.strftime('%Y-%m-%d')
                    elif '-' in card_expiry and len(card_expiry.split('-')[0]) == 2:
                        # من DD-MM-YYYY إلى YYYY-MM-DD
                        date_obj = datetime.strptime(card_expiry, '%d-%m-%Y')
                        card_expiry = date_obj.strftime('%Y-%m-%d')
                    _logger.info(f"Using card expiry date: {card_expiry}")
                except Exception as e:
                    _logger.error(f"Date format error: {e}, using original: {card_expiry}")
            
            with open(debug_file, 'a') as f:
                f.write(f"Card Expiry (original): {original_card_expiry}\n")
                f.write(f"Card Expiry (converted): {card_expiry}\n")
            
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
            url = self.api_base_url  # URL كامل مع المسار
            _logger.info(f"Calling ROP API: {url} for Civil ID: {civil_id} with Card Expiry: {card_expiry}")
            _logger.info(f"SOAP request body: {soap_body}")
            
            with open(debug_file, 'a') as f:
                f.write(f"API URL: {url}\n")
                f.write(f"SOAP Body: {soap_body}\n")
            
            response = requests.post(url, headers=headers, data=soap_body, timeout=self.timeout)
            
            with open(debug_file, 'a') as f:
                f.write(f"Response Status: {response.status_code}\n")
                f.write(f"Response Headers: {dict(response.headers)}\n")
                f.write(f"Response Body: {response.text}\n")
            
            # معالجة الاستجابة
            if response.status_code == 200:
                _logger.info(f"ROP API raw response for Civil ID {civil_id}: {response.text}")
                
                # التحقق من وجود خطأ في الاستجابة حتى لو كان status code 200
                if 'FAILURE' in response.text or 'errorCode' in response.text:
                    _logger.error(f"ROP API returned error in response: {response.text}")
                    with open(debug_file, 'a') as f:
                        f.write(f"ERROR: API returned failure in response\n")
                        f.write(f"Response: {response.text}\n")
                        f.write(f"{'='*80}\n\n")
                    return {
                        'success': False,
                        'error': _('ROP API returned an error: ') + self._extract_error_message(response.text)
                    }
                
                result = self._parse_rop_response(response.text, civil_id, context)
                
                with open(debug_file, 'a') as f:
                    f.write(f"Parse Result: {result}\n")
                    f.write(f"{'='*80}\n\n")
                
                return result
            else:
                _logger.error(f"ROP API error: {response.status_code} - {response.text}")
                with open(debug_file, 'a') as f:
                    f.write(f"ERROR: Status {response.status_code}\n")
                    f.write(f"{'='*80}\n\n")
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

    def _get_language_preference(self, context=None):
        """
        تحديد تفضيل اللغة من السياق أو الإعدادات
        """
        if context:
            # من السياق (مثل lang parameter)
            lang = context.get('lang', '')
            if lang.startswith('ar'):
                return 'ar'
            elif lang.startswith('en'):
                return 'en'
        
        # من إعدادات المستخدم الحالي
        user = self.env.user
        if user.lang:
            if user.lang.startswith('ar'):
                return 'ar'
            elif user.lang.startswith('en'):
                return 'en'
        
        # افتراضي: عربي
        return 'ar'

    def _format_name_by_language(self, name_1, name_2, name_3, name_4, language='ar'):
        """
        تنسيق الاسم حسب اللغة المطلوبة
        """
        if language == 'en':
            # تجميع الاسم الإنجليزي كامل
            return " ".join(filter(None, [name_1, name_2, name_3, name_4])).strip()
        else:
            # تجميع الاسم العربي كامل
            return " ".join(filter(None, [name_1, name_2, name_3, name_4])).strip()

    def _parse_rop_response(self, xml_response, civil_id, context=None):
        """
        تحليل استجابة XML من ROP API مع دعم اللغات
        """
        try:
            _logger.info(f"Parsing ROP response for Civil ID: {civil_id}")
            
            # تحديد اللغة المطلوبة
            language = self._get_language_preference(context)
            _logger.info(f"Using language preference: {language}")
            
            # تنظيف XML وإزالة namespaces
            cleaned_xml = xml_response.replace('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
            cleaned_xml = cleaned_xml.replace('xsi:nil="true"', '')
            
            root = ET.fromstring(cleaned_xml)
            
            # البحث عن Person element في المسار الصحيح
            person = root.find('.//responseBody/Response/Person')
            if person is None:
                return {
                    'success': False,
                    'error': _('No person data found in response')
                }
            
            # استخراج الأسماء من ID_Card/Name (عربية وإنجليزية)
            name_element = person.find('.//ID_Card/Name')
            name_1_ar = self._get_xml_text(name_element, 'name_1_ar') or ''
            name_2_ar = self._get_xml_text(name_element, 'name_2_ar') or ''
            name_3_ar = self._get_xml_text(name_element, 'name_3_ar') or ''
            name_4_ar = self._get_xml_text(name_element, 'name_4_ar') or ''
            
            # الأسماء الإنجليزية
            name_1_en = self._get_xml_text(name_element, 'name_1_en') or ''
            name_2_en = self._get_xml_text(name_element, 'name_2_en') or ''
            name_3_en = self._get_xml_text(name_element, 'name_3_en') or ''
            name_4_en = self._get_xml_text(name_element, 'name_4_en') or ''
            
            # استخراج رقم الهاتف من Address/Permanent
            # البحث عن telephoneNumber أولاً، إذا لم يوجد استخدم mobileNumber
            telephone_number = self._get_xml_text(person, './/Address/Permanent/telephoneNumber')
            mobile_number = self._get_xml_text(person, './/Address/Permanent/mobileNumber')
            
            # تحديد رقم الهاتف النهائي
            phone_number = telephone_number if telephone_number else (mobile_number if mobile_number else '')
            
            # استخراج تاريخ الميلاد من ID_Card/Birth
            birth_date = self._get_xml_text(person, './/ID_Card/Birth/dateOfBirth') or ''
            
            # تحديد اسم العائلة (الجد) - إذا كان name_4 فارغاً استخدم name_3
            family_name_ar = name_4_ar if name_4_ar else name_3_ar
            family_name_en = name_4_en if name_4_en else name_3_en
            
            # تنسيق الاسم حسب اللغة المطلوبة
            if language == 'en':
                # full_name = self._format_name_by_language(name_1_en, name_2_en, name_3_en, name_4_en, 'en')
               
                full_name = name_1_en              
                family_name = family_name_en
            else:
                full_name = name_1_ar
                family_name = family_name_ar
            
            # إعداد البيانات المُستخرجة حسب اللغة
            data = {
                # الاسم الكامل حسب اللغة المطلوبة
                'name': full_name,
                'fourth_name': family_name,
                # معلومات أخرى
                'phone': phone_number,
                'email': '',  # لا يتوفر في API الشرطة
                'civil_id': civil_id,
                'birth_date': birth_date,
                'address': '',  # يمكن إضافته لاحقاً من عنصر Address
                # معلومات إضافية للاستخدام المستقبلي
                'language': language,
                'name_ar': self._format_name_by_language(name_1_ar, name_2_ar, name_3_ar, name_4_ar, 'ar'),
                'name_en': self._format_name_by_language(name_1_en, name_2_en, name_3_en, name_4_en, 'en'),
                'fourth_name_ar': family_name_ar,
                'fourth_name_en': family_name_en,
            }
            
            _logger.info(f"Successfully parsed ROP data with language '{language}': {data}")
            
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
    
    def _extract_error_message(self, xml_response):
        """
        استخراج رسالة الخطأ من استجابة XML
        """
        try:
            root = ET.fromstring(xml_response)
            error_message = root.find('.//errorMessage')
            error_code = root.find('.//errorCode')
            
            if error_message is not None and error_code is not None:
                return f"Code {error_code.text}: {error_message.text}"
            elif error_message is not None:
                return error_message.text
            else:
                return "Unknown error"
        except Exception:
            return "Error parsing response"

    @api.model
    def get_active_config(self):
        """الحصول على الإعداد النشط"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            raise UserError(_('No active Police API configuration found'))
        return config

    def search_visitor_by_data(self, **kwargs):
        """
        البحث في API الشرطة بالبيانات المدخلة
        """
        try:
            # استخراج البيانات من kwargs
            first_name = kwargs.get('first_name', '')
            second_name = kwargs.get('second_name', '')
            third_name = kwargs.get('third_name', '')
            fourth_name = kwargs.get('fourth_name', '')
            phone = kwargs.get('phone', '')
            civil_id = kwargs.get('civil_id', '')
            
            # البحث بالرقم المدني أولاً (إذا كان متوفراً)
            if civil_id:
                result = self.get_visitor_data(civil_id)
                if result.get('success'):
                    return result
            
            # البحث بالهاتف (إذا كان متوفراً)
            if phone:
                # يمكن إضافة منطق البحث بالهاتف هنا
                pass
            
            # البحث بالاسم (إذا كان متوفراً)
            if first_name or second_name or third_name or fourth_name:
                # يمكن إضافة منطق البحث بالاسم هنا
                pass
            
            return {
                'success': False,
                'error': 'No matching data found in police database'
            }
            
        except Exception as e:
            _logger.error(f"Error in search_visitor_by_data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }