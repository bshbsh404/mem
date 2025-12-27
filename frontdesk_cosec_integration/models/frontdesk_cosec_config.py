# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class FrontdeskCosecConfig(models.Model):
    _name = 'frontdesk.cosec.config'
    _description = 'COSEC System Configuration'

    name = fields.Char(string='Configuration Name', required=True)
    active = fields.Boolean(default=True)
    
    # COSEC API Configuration
    api_url = fields.Char(
        string='COSEC API URL', 
        required=True,
        default='https://acixsupport.dvrdns.org:446/COSEC/api.svc/v2/user',
        help='Base URL for COSEC API'
    )
    username = fields.Char(
        string='Username', 
        required=True,
        default='nama',
        help='Username for COSEC API authentication'
    )
    password = fields.Char(
        string='Password', 
        required=True,
        default='Admin@123',
        help='Password for COSEC API authentication'
    )
    
    # Integration Settings
    enable_cosec_integration = fields.Boolean(
        string='Enable COSEC Integration',
        default=True,
        help='Enable sending visitor data to COSEC system'
    )
    
    # Field Mapping
    emp_id_prefix = fields.Char(
        string='Employee ID Prefix',
        default='NAMA',
        help='Prefix to add before employee ID (e.g., NAMA1005)'
    )
    
    # Station Configuration
    station_ids = fields.Many2many(
        'frontdesk.frontdesk',
        string='Frontdesk Stations',
        help='Select which frontdesk stations should send data to COSEC'
    )
    
    # Logging
    enable_logging = fields.Boolean(
        string='Enable Logging',
        default=True,
        help='Log all COSEC API calls for debugging'
    )
    
    @api.model
    def get_active_config(self):
        """Get the active COSEC configuration"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            raise UserError(_('No active COSEC configuration found. Please create one.'))
        return config
    
    def test_connection(self):
        """Test connection to COSEC API"""
        self.ensure_one()
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            # Test URL with proper parameters - using the exact format from the example
            test_url = f"{self.api_url}?action=set;id=TEST001;active=0"
            
            # Make test request
            response = requests.get(
                test_url,
                auth=HTTPBasicAuth(self.username, self.password),
                timeout=30,
                verify=False  # For self-signed certificates
            )
            
            # Always show a message regardless of the result
            response_text = response.text.strip()
            
            if response.status_code == 200:
                # Check if response contains success message
                if ('success' in response_text.lower() or 
                    'saved successfully' in response_text.lower() or
                    '0070200001' in response_text):
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('✅ نجح الاتصال'),
                            'message': _('تم الاتصال بنجاح مع COSEC API!\n\nالاستجابة: %s\n\nالرابط المستخدم: %s') % (response_text, test_url),
                            'type': 'success',
                            'sticky': True,
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('⚠️ تحذير'),
                            'message': _('تم الاتصال لكن الـ API أعطى استجابة غير متوقعة:\n\nالاستجابة: %s\n\nالرابط المستخدم: %s\n\nقد تكون هناك مشكلة في معاملات الـ API.') % (response_text, test_url),
                            'type': 'warning',
                            'sticky': True,
                        }
                    }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('❌ فشل الاتصال'),
                        'message': _('فشل الاتصال مع COSEC API!\n\nرمز الخطأ: %s\n\nالاستجابة: %s\n\nالرابط المستخدم: %s') % (response.status_code, response_text, test_url),
                        'type': 'danger',
                        'sticky': True,
                    }
                }
                
        except requests.exceptions.ConnectionError as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('❌ خطأ في الاتصال'),
                    'message': _('لا يمكن الاتصال بالخادم!\n\nالخطأ: %s\n\nالرابط المستخدم: %s\n\nتأكد من:\n- صحة الرابط\n- اتصال الإنترنت\n- إمكانية الوصول للخادم') % (str(e), self.api_url),
                    'type': 'danger',
                    'sticky': True,
                }
            }
        except requests.exceptions.Timeout as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('⏰ انتهت مهلة الاتصال'),
                    'message': _('انتهت مهلة الاتصال بالخادم!\n\nالرابط المستخدم: %s\n\nقد يكون الخادم بطيء أو غير متاح.') % self.api_url,
                    'type': 'danger',
                    'sticky': True,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('❌ خطأ غير متوقع'),
                    'message': _('حدث خطأ غير متوقع أثناء اختبار الاتصال!\n\nالخطأ: %s\n\nالرابط المستخدم: %s') % (str(e), self.api_url),
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def action_auto_retry_failed_logs(self):
        """Manually trigger auto retry for failed logs"""
        self.ensure_one()
        
        try:
            result = self.env['frontdesk.cosec.log'].auto_retry_failed_logs()
            
            success_count = result.get('success_count', 0)
            error_count = result.get('error_count', 0)
            total_count = result.get('total_count', 0)
            
            if total_count == 0:
                message = "لا توجد سجلات فاشلة لإعادة المحاولة"
                message_type = 'info'
            elif success_count > 0:
                message = f"✅ تم إعادة إرسال {success_count} سجل بنجاح"
                if error_count > 0:
                    message += f"\n❌ فشل في إرسال {error_count} سجل"
                message_type = 'success'
            else:
                message = f"❌ فشل في إعادة إرسال جميع السجلات ({error_count} سجل)"
                message_type = 'warning'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('🔄 إعادة المحاولة التلقائية'),
                    'message': message,
                    'type': message_type,
                    'sticky': True,
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('❌ خطأ في إعادة المحاولة'),
                    'message': f'فشل في إعادة المحاولة التلقائية:\n\n{str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def test_detailed_connection(self):
        """Test connection with different parameters to understand API behavior"""
        self.ensure_one()
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            test_results = []
            test_results.append("🔍 نتائج الاختبار التفصيلي للاتصال مع COSEC API:")
            test_results.append("=" * 50)
            
            # Test 1: Basic connection test
            test_url1 = f"{self.api_url}?action=set;id=TEST001;active=0"
            try:
                response1 = requests.get(
                    test_url1,
                    auth=HTTPBasicAuth(self.username, self.password),
                    timeout=30,
                    verify=False
                )
                test_results.append(f"✅ الاختبار 1 (action=set;id=TEST001;active=0):")
                test_results.append(f"   رمز الحالة: {response1.status_code}")
                test_results.append(f"   الاستجابة: {response1.text.strip()}")
            except Exception as e:
                test_results.append(f"❌ الاختبار 1 فشل: {str(e)}")
            
            test_results.append("")
            
            # Test 2: Test with active=1
            test_url2 = f"{self.api_url}?action=set;id=TEST002;active=1"
            try:
                response2 = requests.get(
                    test_url2,
                    auth=HTTPBasicAuth(self.username, self.password),
                    timeout=30,
                    verify=False
                )
                test_results.append(f"✅ الاختبار 2 (action=set;id=TEST002;active=1):")
                test_results.append(f"   رمز الحالة: {response2.status_code}")
                test_results.append(f"   الاستجابة: {response2.text.strip()}")
            except Exception as e:
                test_results.append(f"❌ الاختبار 2 فشل: {str(e)}")
            
            test_results.append("")
            
            # Test 3: Test with different action
            test_url3 = f"{self.api_url}?action=get;id=TEST003"
            try:
                response3 = requests.get(
                    test_url3,
                    auth=HTTPBasicAuth(self.username, self.password),
                    timeout=30,
                    verify=False
                )
                test_results.append(f"✅ الاختبار 3 (action=get;id=TEST003):")
                test_results.append(f"   رمز الحالة: {response3.status_code}")
                test_results.append(f"   الاستجابة: {response3.text.strip()}")
            except Exception as e:
                test_results.append(f"❌ الاختبار 3 فشل: {str(e)}")
            
            test_results.append("")
            test_results.append("📋 ملاحظات:")
            test_results.append("- إذا كانت جميع الاختبارات تعطي نفس الاستجابة، قد تكون هناك مشكلة في الـ API")
            test_results.append("- إذا كان الاختبار 3 مختلف، قد يكون الـ API يعمل بشكل صحيح")
            test_results.append("- تأكد من صحة بيانات الاعتماد (Username/Password)")
            
            # Return detailed results
            message = "\n".join(test_results)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('🔍 نتائج الاختبار التفصيلي'),
                    'message': message,
                    'type': 'info',
                    'sticky': True,
                }
            }
                
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('❌ فشل الاختبار التفصيلي'),
                    'message': _('حدث خطأ أثناء الاختبار التفصيلي:\n\nالخطأ: %s') % str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
