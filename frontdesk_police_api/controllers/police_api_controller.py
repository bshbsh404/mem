# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class PoliceApiController(http.Controller):

    @http.route('/frontdesk/police_api/get_visitor_data', type='json', auth='public', csrf=False)
    def get_visitor_data_from_police(self, civil_id, card_expiry=None, context=None):
        """
        endpoint للحصول على بيانات الزائر من ROP API مع دعم اللغات
        """
        try:
            # الحصول على إعدادات API
            config = request.env['police.api.config'].sudo().get_active_config()
            
            # إعداد السياق للغة
            if context is None:
                context = {}
            
            # إضافة لغة المستخدم الحالي إذا لم يتم تحديدها
            if 'lang' not in context:
                context['lang'] = request.env.lang or 'ar'
            
            _logger.info(f"Requesting ROP API with language: {context.get('lang', 'ar')}")
            
            # استدعاء ROP API مع السياق
            result = config.get_visitor_data(civil_id, card_expiry, context)
            
            _logger.info(f"ROP API result for civil_id {civil_id}: {result}")
            
            return result
            
        except Exception as e:
            _logger.error(f"Error in ROP API controller: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/frontdesk/police_api/search_visitor', type='json', auth='public', csrf=False)
    def search_visitor(self, **kwargs):
        """
        endpoint للبحث في API الشرطة بالبيانات المدخلة
        """
        try:
            # الحصول على إعدادات API
            config = request.env['police.api.config'].sudo().get_active_config()
            
            # البحث في API الشرطة
            result = config.search_visitor_by_data(**kwargs)
            
            _logger.info(f"Police API search result: {result}")
            
            return result
            
        except Exception as e:
            _logger.error(f"Error in police API search: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }