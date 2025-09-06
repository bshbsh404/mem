from odoo import api, fields, models, _
from datetime import timedelta
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_partner import SignupError, now

import contextlib
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _action_reset_password(self):
        """ create signup token for each user, and send their signup url by email """
        if self.env.context.get('install_mode') or self.env.context.get('import_file'):
            return
        if self.filtered(lambda user: not user.active):
            raise UserError(_("You cannot perform this action on an archived user."))
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        try:
            # Fetch expiration time in minutes from settings
            expiration_minutes = int(
                self.env["ir.config_parameter"].sudo().get_param("auth_signup.token_expiration_minutes", 20)
            )
        except Exception:
            expiration_minutes = 20

        # no time limit for initial invitation, only for reset password
        # expiration = False if create_mode else now(days=+1)
        # Prepare reset password signup with dynamic expiration
        expiration = fields.Datetime.now() + timedelta(minutes=expiration_minutes)

        _logger.info("Token expiration set to %s minutes", expiration_minutes)

        self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        # send email to users with their signup url
        account_created_template = None
        if create_mode:
            account_created_template = self.env.ref('auth_signup.set_password_email', raise_if_not_found=False)
            if account_created_template and account_created_template._name != 'mail.template':
                _logger.error("Wrong set password template %r", account_created_template)
                return

        email_values = {
            'email_cc': False,
            'auto_delete': True,
            'message_type': 'user_notification',
            'recipient_ids': [],
            'partner_ids': [],
            'scheduled_date': False,
        }

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            email_values['email_to'] = user.email
            with contextlib.closing(self.env.cr.savepoint()):
                if account_created_template:
                    account_created_template.send_mail(
                        user.id, force_send=True,
                        raise_exception=True, email_values=email_values)
                else:
                    body = self.env['mail.render.mixin']._render_template(
                        self.env.ref('auth_signup.reset_password_email'),
                        model='res.users', res_ids=user.ids,
                        engine='qweb_view', options={'post_process': True})[user.id]
                    mail = self.env['mail.mail'].sudo().create({
                        'subject': _('Password reset'),
                        'email_from': user.company_id.email_formatted or user.email_formatted,
                        'body_html': body,
                        **email_values,
                    })
                    mail.send()
            _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)