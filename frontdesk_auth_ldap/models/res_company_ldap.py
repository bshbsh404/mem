import ldap
import logging
from ldap.filter import filter_format

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessDenied
from odoo.tools.misc import str2bool
from odoo.tools.pycompat import to_text

_logger = logging.getLogger(__name__)

class CompanyLDAP(models.Model):
    _inherit = 'res.company.ldap'

    def _get_or_create_user(self, conf, login, ldap_entry):
        """
        Retrieve an active resource of model res_users with the specified
        login. Create the user if it is not initially found.

        :param dict conf: LDAP configuration
        :param login: the user's login
        :param tuple ldap_entry: single LDAP result (dn, attrs)
        :return: res_users id
        :rtype: int
        """
        login = tools.ustr(login.lower().strip())
        self.env.cr.execute("SELECT id, active FROM res_users WHERE lower(login)=%s", (login,))
        res = self.env.cr.fetchone()
        if res:
            if res[1]:
                return res[0]
        elif conf['create_user']:
            user_id = False
            _logger.debug("Creating new Odoo user \"%s\" from LDAP" % login)
            values = self._map_ldap_attributes(conf, login, ldap_entry)
            SudoUser = self.env['res.users'].sudo().with_context(no_reset_password=True)
            if conf['user']:
                values['active'] = True
                user_id = SudoUser.browse(conf['user'][0]).copy(default=values).id
            else:
                user_id = SudoUser.create(values).id

            try:
                _logger.debug("New user created")
                _logger.debug(ldap_entry)
                _logger.debug("LDAP Entry Attributes: %s", ldap_entry[1])
                _logger.debug(ldap_entry[1]['cn'][0])
                _logger.debug("user_id")
                _logger.debug(user_id)
                if user_id:
                    _logger.debug("Creating employee record for user")

                    # Create an employee record for the new user
                    self.env['hr.employee'].sudo().create({
                        'name': tools.ustr(ldap_entry[1]['cn'][0]),
                        'user_id': user_id,
                    })
            except Exception as e:
                _logger.error('An error occurred while creating an employee record for user')
                _logger.error(e)

            return user_id

        raise AccessDenied(_("No local user found for LDAP login and not configured to create one"))
    
    # @api.model
    # def sync_ldap_users(self):
    #     """
    #     Synchronize users from LDAP to Odoo without requiring them to log in.
    #     """
    #     try:
    #         _logger.info("Starting LDAP synchronization")
    #         # Fetch LDAP configurations
    #         ldap_configs = self.sudo()._get_ldap_dicts()
    #         _logger.info("Found %s LDAP configurations", len(ldap_configs))
    #         for conf in ldap_configs:
    #             try:
    #                 _logger.info("Synchronizing LDAP server: %s", conf['ldap_server'])
    #                 # Establish a connection to the LDAP server
    #                 conn = self._connect(conf)
    #                 _logger.info("Connected to LDAP server: %s", conf['ldap_server'])

    #                 # Search for users using the LDAP filter
    #                 ldap_filter = conf['ldap_filter'] or '(objectClass=person)'
    #                 _logger.info("LDAP filter: %s", ldap_filter)
    #                 results = self._query(conf, ldap_filter, retrieve_attributes=['uid', 'mail', 'cn'])
    #                 _logger.info("LDAP query returned %s results", len(results))

    #                 # Process each LDAP entry
    #                 for dn, ldap_entry in results:
    #                     _logger.debug("Processing LDAP entry: %s", dn)
    #                     if not dn or not ldap_entry:
    #                         _logger.warning("Skipping invalid LDAP entry: %s", dn)
    #                         continue
    #                     _logger.debug("LDAP entry attributes: %s", ldap_entry)

    #                     # Extract the login field
    #                     login = ldap_entry.get('uid', [b''])[0].decode().strip().lower()
    #                     _logger.debug("LDAP login: %s", login)
    #                     if not login:
    #                         _logger.warning("LDAP entry missing login attribute. Skipping: %s", ldap_entry)
    #                         continue

    #                     # Attempt to create or retrieve the user using existing methods
    #                     try:
    #                         _logger.debug("Attempting to create or retrieve user: %s", login)
    #                         user_id = self._get_or_create_user(conf, login, (dn, ldap_entry))
    #                         _logger.info("Synchronized LDAP user: %s (ID: %s)", login, user_id)
    #                     except AccessDenied:
    #                         _logger.warning("Access denied for LDAP login: %s. Skipping.", login)
    #                     except Exception as e:
    #                         _logger.error("Error processing LDAP user %s: %s", login, e)

    #                     _logger.debug("Finished processing LDAP entry: %s", dn)

    #             except ldap.LDAPError as e:
    #                 _logger.error("Failed to connect or query LDAP server %s: %s", conf['ldap_server'], e)

    #             finally:
    #                 _logger.info("Finished synchronizing LDAP server: %s", conf['ldap_server'])
    #                 if conn:
    #                     _logger.info("Disconnecting from LDAP server: %s", conf['ldap_server'])
    #                     conn.unbind_s()
    #                     _logger.info("Disconnected from LDAP server: %s", conf['ldap_server'])

    #     except Exception as e:
    #         _logger.error("Unexpected error during LDAP synchronization: %s", e)