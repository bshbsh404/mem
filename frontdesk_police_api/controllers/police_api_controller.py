# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class PoliceApiController(http.Controller):

    @http.route('/frontdesk/police_api/get_visitor_data', type='json', auth='public', csrf=False)
    def get_visitor_data_from_police(self, civil_id, card_expiry=None):
        """
        endpoint للحصول على بيانات الزائر من ROP API
        """
        try:
            # الحصول على إعدادات API
            config = request.env['police.api.config'].sudo().get_active_config()
            
            # استدعاء ROP API
            result = config.get_visitor_data(civil_id, card_expiry)
            
            _logger.info(f"ROP API result for civil_id {civil_id}: {result}")
            
            return result
            
        except Exception as e:
            _logger.error(f"Error in ROP API controller: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }