# -*- coding: utf-8 -*-
{
    'name': 'Frontdesk Police API Integration',
    'category': 'Human Resources/Frontdesk',
    'description': '''
        Integration with Police API to fetch visitor data automatically.
        Adds a new visitor type "Police ID" that fetches visitor information
        from the police database.
    ''',
    'summary': 'Police API integration for automatic visitor data retrieval',
    'version': '1.0',
    'depends': ['frontdesk'],  # يعتمد على الموديول الأساسي
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    
    'data': [
        'security/ir.model.access.csv',
        'views/frontdesk_police_config_views.xml',
    ],
    
    'assets': {
        'frontdesk.assets_frontdesk': [
            'frontdesk_police_api/static/src/**/*',
        ],
    },
}