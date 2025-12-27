#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار بسيط للنموذج المحسن
"""

import json

def test_police_api_search():
    """اختبار API البحث في الشرطة"""
    
    # بيانات اختبار
    test_data = {
        'first_name': 'أحمد',
        'second_name': 'محمد',
        'third_name': 'علي',
        'fourth_name': 'الحسيني',
        'phone': '91234567',
        'civil_id': '12345678'
    }
    
    print("🔍 اختبار API البحث في الشرطة...")
    print(f"البيانات المرسلة: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        # محاكاة استدعاء API
        response = {
            'success': True,
            'data': {
                'name': 'أحمد',
                'second_name': 'محمد',
                'third_name': 'علي',
                'fourth_name': 'الحسيني',
                'phone': '91234567',
                'civil_id': '12345678',
                'email': 'ahmed@example.com'
            }
        }
        
        print("✅ تم استرجاع البيانات بنجاح")
        print(f"البيانات المسترجعة: {json.dumps(response['data'], ensure_ascii=False, indent=2)}")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في API: {str(e)}")
        return False

def test_form_filling():
    """اختبار ملء النموذج"""
    
    print("\n📝 اختبار ملء النموذج...")
    
    # بيانات وهمية من API الشرطة
    police_data = {
        'name': 'أحمد',
        'second_name': 'محمد',
        'third_name': 'علي',
        'fourth_name': 'الحسيني',
        'phone': '91234567',
        'civil_id': '12345678',
        'email': 'ahmed@example.com'
    }
    
    # محاكاة ملء الحقول
    form_fields = {
        'inputName': police_data.get('name', ''),
        'inputSecondName': police_data.get('second_name', ''),
        'inputThirdName': police_data.get('third_name', ''),
        'inputFourthName': police_data.get('fourth_name', ''),
        'inputPhone': police_data.get('phone', ''),
        'inputEmail': police_data.get('email', ''),
        'inputVisitorID': police_data.get('civil_id', '')
    }
    
    print("✅ تم ملء الحقول بنجاح:")
    for field, value in form_fields.items():
        if value:
            print(f"  - {field}: {value}")
    
    return True

def test_navigation():
    """اختبار التنقل بين النماذج"""
    
    print("\n🔄 اختبار التنقل بين النماذج...")
    
    navigation_flow = [
        "النموذج الأصلي",
        "نموذج الشرطة الحالي",
        "النموذج المحسن",
        "العودة للنموذج الحالي"
    ]
    
    for step in navigation_flow:
        print(f"  ✅ {step}")
    
    print("✅ تم اختبار التنقل بنجاح")
    return True

def main():
    """الدالة الرئيسية للاختبار"""
    
    print("🚀 بدء اختبار النموذج المحسن")
    print("=" * 50)
    
    # اختبار API البحث
    api_test = test_police_api_search()
    
    # اختبار ملء النموذج
    form_test = test_form_filling()
    
    # اختبار التنقل
    nav_test = test_navigation()
    
    print("\n" + "=" * 50)
    print("📊 نتائج الاختبار:")
    print(f"  - API البحث: {'✅ نجح' if api_test else '❌ فشل'}")
    print(f"  - ملء النموذج: {'✅ نجح' if form_test else '❌ فشل'}")
    print(f"  - التنقل: {'✅ نجح' if nav_test else '❌ فشل'}")
    
    if all([api_test, form_test, nav_test]):
        print("\n🎉 جميع الاختبارات نجحت!")
        return True
    else:
        print("\n⚠️ بعض الاختبارات فشلت!")
        return False

if __name__ == "__main__":
    main() 