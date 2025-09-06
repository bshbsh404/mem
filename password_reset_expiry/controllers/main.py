from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request
from datetime import datetime
import werkzeug
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
import logging

_logger = logging.getLogger(__name__)

class AuthSignupHomeExtended(AuthSignupHome):

    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        _logger.info("in web_auth_reset_password")
        qcontext = self.get_auth_signup_qcontext()

        if qcontext.get('token'):
            _logger.info("token: %s", qcontext.get('token'))
            _logger.info(qcontext)
            # using the token, find the partner and check if the token is expired
            partner = request.env['res.partner'].sudo()._signup_retrieve_partner(qcontext.get('token'), raise_exception=True)
            _logger.info("partner.signup_expiration: %s", partner.signup_expiration)
            if partner.signup_expiration and partner.signup_expiration < datetime.now():
                _logger.info("The password reset token has expired. Please request a new one.")
                # raise werkzeug.exceptions.NotFound()
                # remove the token from the context to avoid the error
                qcontext.pop('token')
                qcontext.pop('login')
                qcontext['error'] = _("The password reset token has expired. Please request a new one.")

                response = request.render('auth_signup.reset_password', qcontext)
                response.headers['X-Frame-Options'] = 'SAMEORIGIN'
                response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
                return response

        # Call the original method to reuse its functionality
        # # If a token is provided, validate its expiration
        # token = request.params.get('token')
        # error = False
        # _logger.info(token)
        # if token:
        #     try:
        #         partner = request.env['res.partner'].sudo()._signup_retrieve_partner(token, raise_exception=True)
        #         _logger.info("partner.signup_expiration: %s", partner.signup_expiration)
        #         _logger.info("datetime.now(): %s", datetime.now())
        #         _logger.info(partner.signup_expiration and partner.signup_expiration < datetime.now())
        #         if partner.signup_expiration and partner.signup_expiration < datetime.now():
        #             # raise UserError(_("The password reset token has expired. Please request a new one."))
        #             _logger.info("The password reset token has expired. Please request a new one.")
        #             _logger.info(partner.signup_expiration)
        #             _logger.info(datetime.now())
        #             _logger.info(token)
        #             error = True
        #     except Exception as e:
        #         _logger.error(e)
        #         error = True
        #         # check if the user is signed in now
        #         if not request.env.user._is_public():
        #             return request.redirect('/web')

        # if error:
        #     raise werkzeug.exceptions.NotFound()

        return super(AuthSignupHomeExtended, self).web_auth_reset_password(*args, **kw)