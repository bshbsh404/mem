# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Frontdesk Azure Sync',
    'category': 'Human Resources/Frontdesk',
    'description': 'Frontdesk Azure Sync',
    'summary': 'Frontdesk Azure Sync',
    'installable': True,
    'application': True,
    'license': 'OEEL-1',
    'version': '1.0',
    'depends': ['frontdesk', 'auth_ldap', 'hr'],
    'data': [
        'views/res_config_settings.xml',
        'data/scheduled_actions.xml',
    ],
}
