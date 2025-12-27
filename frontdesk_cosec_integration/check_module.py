# -*- coding: utf-8 -*-
"""
Module validation script for Frontdesk COSEC Integration
"""

def check_module_structure():
    """Check if all required files exist"""
    import os
    
    required_files = [
        '__manifest__.py',
        '__init__.py',
        'models/__init__.py',
        'models/frontdesk_cosec_config.py',
        'models/frontdesk_cosec_log.py',
        'models/frontdesk_visitor.py',
        'controllers/__init__.py',
        'controllers/main.py',
        'views/frontdesk_cosec_views.xml',
        'data/frontdesk_cosec_data.xml',
        'security/ir.model.access.csv',
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"Missing files: {missing_files}")
        return False
    else:
        print("All required files exist")
        return True

def check_manifest():
    """Check manifest file"""
    try:
        import ast
        
        with open('__manifest__.py', 'r') as f:
            content = f.read()
        
        manifest = ast.literal_eval(content)
        
        required_keys = ['name', 'version', 'depends', 'data']
        missing_keys = [key for key in required_keys if key not in manifest]
        
        if missing_keys:
            print(f"Missing keys in manifest: {missing_keys}")
            return False
        else:
            print("Manifest file is valid")
            return True
            
    except Exception as e:
        print(f"Error checking manifest: {str(e)}")
        return False

def check_models():
    """Check model definitions"""
    try:
        # Check if models can be imported
        import sys
        sys.path.append('.')
        
        from models.frontdesk_cosec_config import FrontdeskCosecConfig
        from models.frontdesk_cosec_log import FrontdeskCosecLog
        from models.frontdesk_visitor import FrontdeskVisitor
        
        print("All models can be imported successfully")
        return True
        
    except Exception as e:
        print(f"Error importing models: {str(e)}")
        return False

def main():
    """Main validation function"""
    print("=== Frontdesk COSEC Integration Module Validation ===")
    
    checks = [
        ("Module Structure", check_module_structure),
        ("Manifest File", check_manifest),
        ("Model Definitions", check_models),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n--- {check_name} ---")
        if not check_func():
            all_passed = False
    
    print(f"\n=== Validation {'PASSED' if all_passed else 'FAILED'} ===")
    return all_passed

if __name__ == "__main__":
    main()





