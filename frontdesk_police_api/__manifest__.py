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
        'web.assets_frontend': [
            'frontdesk_police_api/static/src/police_visitor_form.js',
            'frontdesk_police_api/static/src/police_visitor_form.xml',
            'frontdesk_police_api/static/src/js/police_lookup_shim.js',
        ],
        'web.assets_frontend_lazy': [
            'frontdesk_police_api/static/src/js/police_lookup_shim.js',
        ],
        'frontdesk.assets_frontdesk': [
            'frontdesk_police_api/static/src/visitor_form_extension.xml',
        ],
    },
}