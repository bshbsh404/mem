# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Frontdesk Blacklist',
    'category': 'Human Resources/Frontdesk',
    'description': 'Blacklist management for frontdesk visitors',
    'summary': 'Manage blacklisted visitors in frontdesk',
    'installable': True,
    'application': False,
    'license': 'OEEL-1',
    'version': '1.0',
    'depends': ['frontdesk'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/visitor_blacklist_views.xml',
        'views/res_partner_views.xml',
        'views/frontdesk_menus.xml',
    ],
}