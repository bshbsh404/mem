{
    'name': 'Hide Chatter',
    'version': '17.0',
    'category': 'Discuss',
    'summary': 'Disable the chatter of specific models',
    'description': "Disable the chatter of specific models",
    'depends': ['web'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hide_chatter/static/src/js/form_arch_parser.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
