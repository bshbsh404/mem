/** @odoo-module **/

import { VisitorForm } from "@frontdesk/visitor_form/visitor_form";
import { patch } from "@web/core/utils/patch";

// إضافة امتداد لنموذج الزائر لدعم API الشرطة
patch(VisitorForm.prototype, {
    setup() {
        super.setup();
        // إضافة متغيرات جديدة للحالة
        this.state.isPoliceApiLoading = false;
        this.state.policeApiError = null;
        // إضافة مرجع لحقل تاريخ انتهاء البطاقة
        this.inputCardExpiryRef = useRef("inputCardExpiry");
    },

    /**
     * دالة جديدة للبحث في قاعدة بيانات الشرطة العمانية (ROP)
     */
    async _onPoliceIdLookup() {
        const civilId = this.inputVisitorIDRef.el?.value;
        const cardExpiry = this.inputCardExpiryRef.el?.value;
        
        if (!civilId || civilId.length < 8) {
            this.state.policeApiError = "يرجى إدخال رقم البطاقة المدنية صحيح (8 أرقام على الأقل)";
            return;
        }

        if (!cardExpiry) {
            this.state.policeApiError = "يرجى إدخال تاريخ انتهاء البطاقة";
            return;
        }

        this.state.isPoliceApiLoading = true;
        this.state.policeApiError = null;

        try {
            console.log("البحث في قاعدة بيانات الشرطة العمانية عن:", civilId, "تاريخ الانتهاء:", cardExpiry);
            
            const result = await this.rpc("/frontdesk/police_api/get_visitor_data", {
                civil_id: civilId,
                card_expiry: cardExpiry
            });

            if (result.success && result.data) {
                // ملء البيانات تلقائياً
                this._fillVisitorDataFromPolice(result.data);
                
                // إظهار رسالة نجاح
                this.state.policeApiError = null;
                console.log("تم استرجاع البيانات بنجاح من الشرطة العمانية:", result.data);
                
            } else {
                this.state.policeApiError = result.error || "لم يتم العثور على البيانات في قاعدة بيانات الشرطة";
            }

        } catch (error) {
            console.error("خطأ في استدعاء ROP API:", error);
            this.state.policeApiError = "حدث خطأ في الاتصال بقاعدة بيانات الشرطة العمانية";
        } finally {
            this.state.isPoliceApiLoading = false;
        }
    },

    /**
     * ملء بيانات النموذج من البيانات المسترجعة من الشرطة
     */
    _fillVisitorDataFromPolice(data) {
        // ملء الأسماء
        if (data.name && this.inputNameRef.el) {
            this.inputNameRef.el.value = data.name;
        }
        if (data.second_name && this.inputSecondNameRef.el) {
            this.inputSecondNameRef.el.value = data.second_name;
        }
        if (data.third_name && this.inputThirdNameRef.el) {
            this.inputThirdNameRef.el.value = data.third_name;
        }
        if (data.fourth_name && this.inputFourthNameRef.el) {
            this.inputFourthNameRef.el.value = data.fourth_name;
        }

        // ملء رقم الهاتف
        if (data.phone && this.inputPhoneRef.el) {
            this.inputPhoneRef.el.value = data.phone;
        }

        // ملء البريد الإلكتروني
        if (data.email && this.inputEmailRef.el) {
            this.inputEmailRef.el.value = data.email;
        }

        // تحديث رقم البطاقة (في حالة التنسيق)
        if (data.civil_id && this.inputVisitorIDRef.el) {
            this.inputVisitorIDRef.el.value = data.civil_id;
        }

        // إظهار رسالة نجاح
        console.log("تم ملء البيانات تلقائياً من قاعدة بيانات الشرطة");
    },

    /**
     * دالة للتحقق من تغيير نوع الزائر
     */
    _onVisitorTypeChange(ev) {
        super._onVisitorTypeChange(ev);
        
        // إذا تم اختيار نوع "police_id" يمكن إضافة منطق خاص
        if (ev.target.value === 'police_id') {
            console.log("تم اختيار نوع زائر: بحث في قاعدة بيانات الشرطة");
        }
    }
});