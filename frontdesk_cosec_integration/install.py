# -*- coding: utf-8 -*-
"""
Installation script for Frontdesk COSEC Integration module
"""

def install(env):
    """Install the module"""
    try:
        # Create default configuration if not exists
        config = env['frontdesk.cosec.config'].search([('active', '=', True)], limit=1)
        if not config:
            env['frontdesk.cosec.config'].create({
                'name': 'Default COSEC Configuration',
                'active': True,
                'api_url': 'https://acixsupport.dvrdns.org:446/COSEC/api.svc/v2/user',
                'username': 'nama',
                'password': 'Admin@123',
                'enable_cosec_integration': True,
                'emp_id_prefix': 'NAMA',
                'enable_logging': True,
            })
            print("Default COSEC configuration created successfully")
        
        print("Frontdesk COSEC Integration module installed successfully")
        return True
        
    except Exception as e:
        print(f"Error installing module: {str(e)}")
        return False

def uninstall(env):
    """Uninstall the module"""
    try:
        # Clean up any module-specific data if needed
        print("Frontdesk COSEC Integration module uninstalled successfully")
        return True
        
    except Exception as e:
        print(f"Error uninstalling module: {str(e)}")
        return False
