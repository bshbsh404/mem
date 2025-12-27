#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تشخيص مشكلة عدم ظهور الأيقونة
"""

import os
import re

def check_file_exists(file_path):
    """التحقق من وجود الملف"""
    if os.path.exists(file_path):
        print(f"✅ {file_path} - موجود")
        return True
    else:
        print(f"❌ {file_path} - غير موجود")
        return False

def check_icon_in_xml(file_path):
    """التحقق من وجود الأيقونة في ملف XML"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # البحث عن الأيقونة
        icon_patterns = [
            r'Open Enhanced Form',
            r'_goToEnhancedPoliceForm',
            r'fa fa-star',
            r'btn-success'
        ]
        
        found_patterns = []
        for pattern in icon_patterns:
            if re.search(pattern, content):
                found_patterns.append(pattern)
                print(f"✅ وجد: {pattern}")
            else:
                print(f"❌ لم يجد: {pattern}")
        
        return len(found_patterns) == len(icon_patterns)
        
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {str(e)}")
        return False

def check_function_in_js(file_path):
    """التحقق من وجود الدالة في ملف JavaScript"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if '_goToEnhancedPoliceForm' in content:
            print("✅ دالة _goToEnhancedPoliceForm موجودة")
            return True
        else:
            print("❌ دالة _goToEnhancedPoliceForm غير موجودة")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {str(e)}")
        return False

def check_manifest():
    """التحقق من ملف __manifest__.py"""
    manifest_path = 'frontdesk_police_api/__manifest__.py'
    
    if not check_file_exists(manifest_path):
        return False
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'frontdesk_police_api/static/src/**/*' in content:
            print("✅ assets pattern موجود في __manifest__.py")
            return True
        else:
            print("❌ assets pattern غير موجود في __manifest__.py")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في قراءة __manifest__.py: {str(e)}")
        return False

def main():
    """الدالة الرئيسية للتشخيص"""
    
    print("🔍 تشخيص مشكلة عدم ظهور الأيقونة")
    print("=" * 50)
    
    # التحقق من وجود الملفات
    print("\n📁 التحقق من وجود الملفات:")
    xml_exists = check_file_exists('frontdesk_police_api/static/src/visitor_form_police_extension.xml')
    js_exists = check_file_exists('frontdesk_police_api/static/src/visitor_form_police_extension.js')
    manifest_exists = check_file_exists('frontdesk_police_api/__manifest__.py')
    
    # التحقق من محتوى الملفات
    print("\n📄 التحقق من محتوى الملفات:")
    xml_ok = check_icon_in_xml('frontdesk_police_api/static/src/visitor_form_police_extension.xml')
    js_ok = check_function_in_js('frontdesk_police_api/static/src/visitor_form_police_extension.js')
    manifest_ok = check_manifest()
    
    # التحقق من الملفات الجديدة
    print("\n🆕 التحقق من الملفات الجديدة:")
    enhanced_xml_exists = check_file_exists('frontdesk_police_api/static/src/enhanced_police_visitor_form.xml')
    enhanced_js_exists = check_file_exists('frontdesk_police_api/static/src/enhanced_police_visitor_form.js')
    
    # النتائج
    print("\n" + "=" * 50)
    print("📊 نتائج التشخيص:")
    
    all_files_exist = all([xml_exists, js_exists, manifest_exists, enhanced_xml_exists, enhanced_js_exists])
    all_content_ok = all([xml_ok, js_ok, manifest_ok])
    
    print(f"  - وجود الملفات: {'✅' if all_files_exist else '❌'}")
    print(f"  - صحة المحتوى: {'✅' if all_content_ok else '❌'}")
    
    if all_files_exist and all_content_ok:
        print("\n✅ جميع الملفات موجودة وصحيحة")
        print("\n🔧 الحلول المقترحة:")
        print("1. امسح cache المتصفح (Ctrl+F5)")
        print("2. أعد تشغيل خادم Odoo")
        print("3. تأكد من تحديث الموديول في Odoo")
        print("4. تحقق من console المتصفح للأخطاء")
    else:
        print("\n❌ هناك مشاكل في الملفات")
        print("يرجى إعادة إنشاء الملفات المفقودة أو تصحيح المحتوى")

if __name__ == "__main__":
    main() 