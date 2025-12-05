import logging
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class OutlookAuthController(http.Controller):

    @http.route('/azure-connect', type='http', auth='user', website=True)
    def azure_connect_callback(self, **kw):
        code = kw.get('code')
        state = kw.get('state')
        error = kw.get('error')
        error_description = kw.get('error_description')
        
        if error:
            _logger.error(f"OAuth error: {error} - {error_description}")
            return request.redirect('/web#action=&model=hr.employee&view_type=form&cids=&menu_id=')
        
        if not code:
            _logger.error("No authorization code received")
            return request.redirect('/web#action=&model=hr.employee&view_type=form&cids=&menu_id=')
        
        if not state:
            _logger.error("No employee ID in state parameter")
            return request.redirect('/web#action=&model=hr.employee&view_type=form&cids=&menu_id=')
        
        employee = request.env['hr.employee'].sudo().browse(int(state))
        
        if not employee.exists():
            _logger.error(f"No employee found with ID {state}")
            return request.redirect('/web#action=&model=hr.employee&view_type=form&cids=&menu_id=')
        
        outlook_config = request.env['outlook.config'].sudo().search([('active', '=', True)], limit=1)
        if not outlook_config:
            _logger.error("No active Outlook configuration found")
            return request.redirect('/web#action=&model=hr.employee&view_type=form&cids=&menu_id=')
        
        token_data = outlook_config.get_access_token(code)
        if token_data:
            expires_in = token_data.get('expires_in', 3600)
            expiry_time = datetime.now() + timedelta(seconds=expires_in)
            employee.sudo().write({
                'outlook_access_token': token_data.get('access_token'),
                'outlook_refresh_token': token_data.get('refresh_token'),
                'outlook_token_expiry': expiry_time,
            })
            _logger.info(f"Successfully authorized Outlook for employee {employee.name}")
        else:
            _logger.error(f"Failed to get access token for employee {employee.name}")
        
        return request.redirect(f'/web#id={employee.id}&model=hr.employee&view_type=form')
