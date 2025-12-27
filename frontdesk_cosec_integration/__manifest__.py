{
    'name': 'Frontdesk COSEC Integration',
    'version': '1.0',
    'category': 'Frontdesk',
    'summary': 'Integration with COSEC System for visitor management',
    'description': """
        This module integrates with COSEC System to send visitor data (emp_id and qr_string) 
        when a new visit is created.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['frontdesk'],
    'data': [
        'security/ir.model.access.csv',
        'views/frontdesk_cosec_views.xml',
        'data/frontdesk_cosec_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

