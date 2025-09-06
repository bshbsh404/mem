# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Frontdesk Outlook Integration',
    'category': 'Human Resources/Frontdesk',
    'description': 'Microsoft Outlook calendar integration for frontdesk visits',
    'summary': 'Sync frontdesk visits with Outlook calendar',
    'installable': True,
    'application': False,
    'license': 'OEEL-1',
    'version': '1.0',
    'depends': ['frontdesk'],
    'data': [
        'security/ir.model.access.csv',
        'views/frontdesk_visitor_views.xml',
        'views/hr_employee_views.xml',
        'data/outlook_config_data.xml',
    ],
    'external_dependencies': {
        'python': ['requests', 'msal'],
    },
}