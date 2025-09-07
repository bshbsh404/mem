# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Frontdesk Visitor API',
    'category': 'Human Resources/Frontdesk',
    'description': '''
        API endpoints for frontdesk visitor approvals.
        Provides REST API endpoints for retrieving approval lists 
        and approving/rejecting visitor requests.
    ''',
    'summary': 'Visitor approval REST API endpoints',
    'version': '1.0',
    'depends': ['frontdesk'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    
    'data': [
        'security/ir.model.access.csv',
    ],
    
    'test': [
        'tests/test_visitor_api.py',
    ],
}