# -*- coding: utf-8 -*-

{
    "name": "Signup Token Expiration",
    "summary": """
       Make password reset token expiration configurable""",
    "author": "Fusion",
    "maintainer": "Fusion",
    "category": "Tools",
    "version": "17.0",
    "license": "AGPL-3",
    'depends': ['auth_signup'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    "installable": True,
}
