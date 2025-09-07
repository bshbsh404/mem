# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Frontdesk Push Notifications',
    'category': 'Human Resources/Frontdesk',
    'description': '''
        Push notification integration for frontdesk module.
        Automatically sends push notifications to employees when 
        new visit requests are created.
    ''',
    'summary': 'Push notification integration for visitor requests',
    'version': '1.0',
    'depends': ['frontdesk'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    
    'data': [
        'security/ir.model.access.csv',
        'views/push_notification_config_views.xml',
    ],
}