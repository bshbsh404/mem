import requests
import logging
from odoo import models, api, fields

_logger = logging.getLogger(__name__)

class AzureADSync(models.Model):
    _name = 'azure.ad.sync'
    _description = 'Azure AD Sync'

    @api.model
    def fetch_and_sync_users(self):
        """
        Scheduled action to fetch all users from Azure AD and create users and employees in Odoo.
        """
        _logger.info("Azure AD sync started.")
        _logger.info("Current user: %s", self.env.user.login)
        _logger.info("Current time: %s", fields.Datetime.now())

        try:
            # Step 1: Get Azure AD access token
            access_token = self._get_azure_ad_token()
            if not access_token:
                _logger.error("Failed to retrieve Azure AD access token. Aborting sync.")
                return

            _logger.info("Successfully retrieved Azure AD access token.")

            # Step 2: Fetch users from Azure AD
            users = self._get_azure_ad_users(access_token)
            if not users:
                _logger.warning("No users retrieved from Azure AD.")
                return

            _logger.info("Retrieved %d users from Azure AD.", len(users))

            try:
                azure_ad_emails = {user.get("mail") for user in users if user.get("mail")}
                # Step 3: Archive users and employees not found in Azure AD
                odoo_users = self.env['res.users'].sudo().search([('created_by_azure', '=', True)])
                for odoo_user in odoo_users:
                    if odoo_user.login not in azure_ad_emails:
                        # Archive the user and their employee
                        try:
                            employee = self.env['hr.employee'].sudo().search([('user_id', '=', odoo_user.id)], limit=1)
                            if employee:
                                employee.active = False
                            odoo_user.active = False
                            _logger.info("Archived user and employee: %s", odoo_user.login)
                        except Exception as e:
                            _logger.error("Failed to archive user '%s': %s", odoo_user.login, e, exc_info=True)
            except Exception as e:
                _logger.error("Failed to archive users not found in Azure AD: %s", e, exc_info=True)

            # Step 4: Sync users and employees in Odoo
            for user_data in users:
                try:
                    self._sync_user(user_data)
                except Exception as user_error:
                    _logger.error(
                        "Error syncing user %s: %s",
                        user_data.get("mail", "unknown email"),
                        user_error,
                        exc_info=True,
                    )

            _logger.info("Azure AD sync completed successfully.")

        except requests.exceptions.RequestException as request_error:
            _logger.error("Error connecting to Azure AD: %s", request_error, exc_info=True)
        except Exception as e:
            _logger.error("Unexpected error during Azure AD sync: %s", e, exc_info=True)

    def _get_azure_ad_token(self):
        """
        Retrieve an access token from Azure AD.
        """
        tenant_id = self.env['ir.config_parameter'].sudo().get_param('azure_ad.tenant_id')
        client_id = self.env['ir.config_parameter'].sudo().get_param('azure_ad.client_id')
        client_secret = self.env['ir.config_parameter'].sudo().get_param('azure_ad.client_secret')

        if not all([tenant_id, client_id, client_secret]):
            _logger.error("Azure AD configuration parameters are missing. Please configure them in system settings.")
            return None

        try:
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            token_response = requests.post(token_url, data={
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'client_credentials',
                'scope': 'https://graph.microsoft.com/.default',
            })
            token_response.raise_for_status()
            return token_response.json().get("access_token")
        except requests.exceptions.RequestException as e:
            _logger.error("Error retrieving Azure AD token: %s", e, exc_info=True)
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

    def _sync_user(self, user_data):
        """
        Sync a single user from Azure AD with Odoo.
        """
        _logger.info("Syncing user: %s", user_data)
        email = user_data.get("mail")
        name = user_data.get("displayName", "Unknown")
        phone = user_data.get("businessPhones", [])
        phone = phone[0] if phone and len(phone) > 0 else None
        department_name = user_data.get("department")
        office_location = (user_data.get("officeLocation") or "").strip()

        if not email:
            _logger.warning("Skipping Azure AD user because email is missing: %s", user_data)
            return
        
        building = False
        if office_location:
            # search for the office location in owwsc.building
            building = self.env['owwsc.building'].sudo().search([('name', '=', office_location)], limit=1)
        
        # Check if the user already exists in Odoo
        existing_user = self.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if existing_user:
            _logger.info("User already exists in Odoo. Skipping: %s", email)
            user = existing_user
            if user and building and building.operating_unit_id:
                _logger.info("User already exists in Odoo. Updating operating unit to: %s", building.operating_unit_id.name)
                # update user operating_unit_ids with operating_unit from the building
                user.write({'operating_unit_ids': [(4, building.operating_unit_id.id)]})
        else:
            user = self._create_or_update_user(email, name)
            if user and building and building.operating_unit_id:
                _logger.info("User created in Odoo. Updating operating unit to: %s", building.operating_unit_id.name)
                user.write({'operating_unit_ids': [(4, building.operating_unit_id.id)]})

        if user:
            self._create_or_update_employee(user, user_data)

    def _create_or_update_user(self, email, name):
        """
        Create or update a user in Odoo.
        """
        user = self.env['res.users'].sudo().search([('login', '=', email)], limit=1)
        if not user:
            template_user_id = int(self.env['ir.config_parameter'].sudo().get_param('azure_ad.azure_user_id'))
            template_user = self.env['res.users'].sudo().browse(template_user_id)
            if template_user:
                _logger.info("Creating new Odoo user using template: %s", template_user.login)
                user = self.env['res.users'].sudo().create({
                    'name': name,
                    'login': email,
                    'email': email,
                    'active': True,
                    'created_by_azure': True,
                    'groups_id': [(6, 0, template_user.groups_id.ids)],
                })
            else:
                user = self.env['res.users'].sudo().create({
                'name': name,
                'login': email,
                'email': email,
                'active': True,
                'created_by_azure': True,
                })
                
            _logger.info("Created new Odoo user: %s", email)
        else:
            _logger.info("User already exists: %s", email)
        return user

    def _create_or_update_employee(self, user, user_data):
        """
        Create or update an employee in Odoo with additional Azure AD fields.
        """
        try:
            # Extract fields from Azure AD user data
            email = user_data.get("mail")
            name = user_data.get("displayName", "Unknown")

            phone = user_data.get("businessPhones", [])
            phone = phone[0] if phone and len(phone) > 0 else None

            department_name = (user_data.get("department") or "").strip()
            job_title = (user_data.get("jobTitle") or "").strip()

            mobile_phone = user_data.get("mobilePhone")
            mobile_phone = mobile_phone if mobile_phone else ""

            # mobile_phone = (user_data.get("mobilePhone") or "").strip()
            office_location = (user_data.get("officeLocation") or "").strip()

            # Ensure the department exists
            department = None
            if department_name:
                department = self.env['hr.department'].sudo().search([('name', '=', department_name)], limit=1)
                if not department:
                    department = False

            _logger.info("Processing employee for user: %s", email)

            # Validate email and user
            if not email:
                _logger.warning("Skipping employee creation. because email is missing.")
                return

            if not user:
                _logger.error("Skipping employee creation. User is not provided.")
                return

            # Check if the employee already exists
            employee = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            

            # check office location
            building = False
            if office_location:
                # search for the office location in owwsc.building
                building = self.env['owwsc.building'].sudo().search([('name', '=', office_location)], limit=1)
                if building:
                    building = building.id

            if not employee:
                # Create the employee with additional fields
                try:
                    self.env['hr.employee'].sudo().create({
                        'name': name,
                        'work_email': email,
                        'work_phone': phone,
                        'mobile_phone': mobile_phone,
                        'job_title': job_title,
                        'user_id': user.id,
                        'department_id': department.id if department else False,
                        'building_id': building,
                    })
                    _logger.info("Created new employee for user: %s", email)
                except Exception as e:
                    _logger.error("Failed to create employee for user '%s': %s", email, e, exc_info=True)
            else:
                # Update the existing employee with new data
                updates = {
                    'work_email': email,
                    'work_phone': phone,
                    'mobile_phone': mobile_phone,
                    'job_title': job_title,
                    'department_id': department.id if department else False,
                    'building_id': building,
                }
                try:
                    employee.sudo().write(updates)
                    _logger.info("Updated employee for user: %s", email)
                except Exception as e:
                    _logger.error("Failed to update employee for user '%s': %s", email, e, exc_info=True)

        except Exception as e:
            _logger.error("Unexpected error while syncing employee for user '%s': %s", user_data.get("mail", "unknown email"), e, exc_info=True)