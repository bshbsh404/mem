/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// دالة تساعدنا نطبّق الباتش على الكلاس المطلوب إن وجد
function patchPoliceScreen(ScreenClass) {
    if (!ScreenClass || ScreenClass.prototype._policeApiPatched) return;
    ScreenClass.prototype._policeApiPatched = true;

    patch(ScreenClass.prototype, "police_api_extension", {
            setup() {
            this._super(...arguments);

            // خدمة RPC الرسمية
            this.rpc = useService("rpc");
            
            // التأكد من أن visitorType معرف
            this.state.visitorType ??= 'individual';
            
            // إضافة مراقب لتغييرات visitorType
            console.log("🔍 Current visitorType:", this.state.visitorType);

            // IMPORTANT: طابق أسماء الـ refs مع القالب
            // القالب يستخدم t-ref="inputPoliceCivilID" و t-ref="inputCardExpiry"
            this.inputPoliceCivilIDRef = useRef("inputPoliceCivilID");
        this.inputCardExpiryRef = useRef("inputCardExpiry");

            // حقول حالة إضافية مطلوبة للرسائل والكارد
            this.state.isPoliceApiLoading ??= false;
            this.state.policeApiError ??= null;
            this.state.policeDataFound ??= false;

            this.state.visitorName ??= "";
            this.state.visitorSecondName ??= "";
            this.state.visitorThirdName ??= "";
            this.state.visitorFourthName ??= "";
            this.state.visitorNameEn ??= "";
            this.state.visitorSecondNameEn ??= "";
            this.state.visitorThirdNameEn ??= "";
            this.state.visitorFourthNameEn ??= "";
            this.state.visitorPhone ??= "";
            this.state.visitorID ??= "";
            this.state.visitorBirthDate ??= "";
            this.state.visitorEmail ??= "";
            
            // مراقبة تغييرات visitorType
            this._originalOnVisitorTypeChange = this._onVisitorTypeChange;
            this._onVisitorTypeChange = (event) => {
                if (this._originalOnVisitorTypeChange) {
                    this._originalOnVisitorTypeChange(event);
                }
                console.log("🔍 visitorType changed to:", this.state.visitorType);
                // إجبار إعادة رسم الواجهة
                this.render?.();
            };
            
            // إضافة مراقب مباشر لـ radio buttons
            this._setupVisitorTypeWatcher();
        },
        
        _setupVisitorTypeWatcher() {
            // مراقبة تغييرات radio buttons مباشرة
            const radioButtons = document.querySelectorAll('input[name="visitorType"]');
            radioButtons.forEach(radio => {
                radio.addEventListener('change', (event) => {
                    console.log("🔍 Radio button changed to:", event.target.value);
                    this.state.visitorType = event.target.value;
                    
                    // التحكم في الظهور باستخدام CSS
                    const policeSection = document.querySelector('.police-search-section');
                    if (policeSection) {
                        if (event.target.value === 'individual' || event.target.value === 'company') {
                            policeSection.style.display = 'block';
                        } else {
                            policeSection.style.display = 'none';
                        }
                    }
                    
                    this.render?.();
                });
            });
            
            // تطبيق الحالة الأولية
            setTimeout(() => {
                const selectedRadio = document.querySelector('input[name="visitorType"]:checked');
                if (selectedRadio && selectedRadio.value !== 'individual' && selectedRadio.value !== 'company') {
                    const policeSection = document.querySelector('.police-search-section');
                    if (policeSection) {
                        policeSection.style.display = 'none';
                    }
                }
            }, 100);
        },

        async _onPoliceIdLookup(ev) {
            ev?.preventDefault?.();

            const civilId = this.inputPoliceCivilIDRef.el?.value?.trim();
            const cardExpiry = this.inputCardExpiryRef.el?.value;

            if (!civilId || civilId.length < 4) {
                this.state.policeApiError = "يرجى إدخال رقم البطاقة المدنية صحيح";
                return;
            }
            if (!cardExpiry) {
                this.state.policeApiError = "يرجى إدخال تاريخ انتهاء البطاقة";
                return;
            }

            this.state.isPoliceApiLoading = true;
            this.state.policeApiError = null;

            try {
                const result = await this.rpc("/frontdesk/police_api/get_visitor_data", {
                    civil_id: civilId,
                    card_expiry: cardExpiry,
                    context: { lang: this.props.currentLang || "ar" },
                });

                if (result?.success && result?.data) {
                    this._fillVisitorDataFromPolice(result.data);
                    this.state.policeDataFound = true;
                } else {
                    this.state.policeApiError = result?.error || "لم يتم العثور على البيانات";
                    this.state.policeDataFound = false;
                }
            } catch (e) {
                console.error("خطأ في API الشرطة:", e);
                this.state.policeApiError = "خطأ في الاتصال بقاعدة بيانات الشرطة";
                this.state.policeDataFound = false;
            } finally {
                this.state.isPoliceApiLoading = false;
            }
        },

        _fillVisitorDataFromPolice(data) {
            // عدّل أسماء المفاتيح حسب استجابة API الفعلية
            const firstName  = data?.name || "";
            const secondName = data?.second_name || "";
            const thirdName  = data?.third_name || "";
            const familyName = data?.fourth_name || "";
            const phone      = data?.phone || "";
            const email      = data?.email || "";

            // تعبئة الحقول في النموذج (إن كانت موجودة)
            this.inputNameRef?.el && (this.inputNameRef.el.value = firstName);
            this.inputSecondNameRef?.el && (this.inputSecondNameRef.el.value = secondName);
            this.inputThirdNameRef?.el && (this.inputThirdNameRef.el.value = thirdName);
            this.inputFourthNameRef?.el && (this.inputFourthNameRef.el.value = familyName);
            this.inputPhoneRef?.el && (this.inputPhoneRef.el.value = phone);
            this.inputEmailRef?.el && (this.inputEmailRef.el.value = email);

            // تحديث الحالة لعرض الكارد الأخضر
            Object.assign(this.state, {
                visitorName: firstName,
                visitorSecondName: secondName,
                visitorThirdName: thirdName,
                visitorFourthName: familyName,
                visitorPhone: phone,
                visitorEmail: email,
                visitorID: this.inputPoliceCivilIDRef.el?.value || "",
            });
        },
    });
}

// طبّق الباتش على الشاشة الصحيحة
const applyPatch = () => {
    const cat = registry.category("frontdesk_screens");
    // جرّب أولًا PoliceVisitorForm (القالب الذي عندك)
    patchPoliceScreen(cat.get("PoliceVisitorForm"));
    // ولو تحب نفس السلوك في النموذج العادي أيضًا:
    patchPoliceScreen(cat.get("VisitorForm"));
};

// تطبيق patch بعد تحميل الصفحة
window.addEventListener('load', () => {
    setTimeout(applyPatch, 1000);
});

// الحل البديل: إضافة الهاندلر على جميع الكومبوننتات
import { Component } from "@odoo/owl";

// اجعل الهاندلر متاحًا على جميع الكومبوننتات مرة واحدة
if (!Component.prototype._policeApiShimAdded) {
    Component.prototype._policeApiShimAdded = true;

    Component.prototype._onPoliceIdLookup = async function (ev) {
        ev?.preventDefault?.();

        // للتشخيص: نعرف أي كومبوننت يملك الزر
        try { console.log("[PoliceLookup] owner component:", this.constructor?.name); } catch(_) {}

        // حضّر state لو غير معرف
        this.state = this.state || {};
        this.state.policeApiError = null;

        // التقاط القيم من refs إن وُجدت، وإلا من الـ DOM بالـ id
        const civilId =
            this.inputPoliceCivilIDRef?.el?.value?.trim?.() ||
            this.inputVisitorID?.el?.value?.trim?.() ||
            document.getElementById("police_civil_id")?.value?.trim?.();

        const cardExpiry =
            this.inputCardExpiryRef?.el?.value ||
            document.getElementById("card_expiry")?.value;
        
        if (!civilId || civilId.length < 4) {
            this.state.policeApiError = "يرجى إدخال رقم البطاقة المدنية صحيح";
            this.render?.();
            return;
        }
        if (!cardExpiry) {
            this.state.policeApiError = "يرجى إدخال تاريخ انتهاء البطاقة";
            this.render?.();
            return;
        }

        this.state.isPoliceApiLoading = true;
        this.render?.();

        try {
            // خدمة RPC من الـ env (أو this.rpc إن كانت مفعّلة)
            const rpc = this.env?.services?.rpc || this.rpc;
            console.log("🔍 RPC service found:", !!rpc);
            
            const result = await rpc("/frontdesk/police_api/get_visitor_data", {
                civil_id: civilId,
                card_expiry: cardExpiry,
                context: { lang: this.props?.currentLang || "ar" },
            });

            console.log("🔍 API Response received:", result);

            if (result?.success && result?.data) {
                const d = result.data || {};
                const firstName  = d.name || "";
                const secondName = d.second_name || "";
                const thirdName  = d.third_name || "";
                const familyName = d.fourth_name || "";
                const phone      = d.phone || "";
                const email      = d.email || "";

                console.log("🔍 Raw API Response:", result);
                console.log("🔍 Extracted Data:", { firstName, secondName, thirdName, familyName, phone, email });

                // تحديث الحالة لعرض الكارد الأخضر
                Object.assign(this.state, {
                    policeDataFound: true,
                    visitorName: firstName,
                    visitorSecondName: secondName,
                    visitorThirdName: thirdName,
                    visitorFourthName: familyName,
                    visitorPhone: phone,
                    visitorEmail: email,
                    visitorID: civilId,
                });

                // ✅ تحديث props.visitorData للنموذج الرئيسي
                if (this.props?.visitorData) {
                    Object.assign(this.props.visitorData, {
                        visitorName: firstName,
                        visitorSecondName: secondName,
                        visitorThirdName: thirdName,
                        visitorFourthName: familyName,
                        visitorPhone: phone,
                        visitorEmail: email,
                        visitorID: civilId,
                    });
                    
                    // ✅ تفعيل reactivity في OWL
                    if (this.props.setVisitorData) {
                        // إذا كان هناك دالة setVisitorData، استخدمها
                        this.props.setVisitorData(
                            firstName,
                            secondName,
                            thirdName,
                            familyName,
                            phone,
                            false, // landline
                            email,
                            false, // company
                            civilId,
                            false, // passport
                            false  // emp_id
                        );
                    }
                }

                // ✅ تفعيل reactivity بإرسال events على الحقول
                const fields = [
                    { id: 'name', value: firstName },
                    { id: 'second_name', value: secondName },
                    { id: 'third_name', value: thirdName },
                    { id: 'fourth_name', value: familyName },
                    { id: 'phone', value: phone },
                    { id: 'email', value: email },
                    { id: 'visitor_id', value: civilId }
                ];
                
                fields.forEach(field => {
                    const element = document.getElementById(field.id);
                    if (element) {
                        element.value = field.value;
                        // إرسال events لتفعيل reactivity
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                        console.log(`✅ Updated field ${field.id} with value: ${field.value}`);
                    }
                });

                // ✅ طباعة في الكونسول
                console.log("✅ Data found successfully! Form filled automatically.");
                console.log("📌 Visitor Data:", {
                    visitorName: firstName,
                    visitorSecondName: secondName,
                    visitorThirdName: thirdName,
                    visitorFourthName: familyName,
                    visitorPhone: phone,
                    visitorEmail: email,
                    visitorID: civilId
                });
                console.log("📌 Props.visitorData updated:", this.props?.visitorData);
                
                // ✅ تحديث الواجهة
                if (this.render) {
                this.render();
                }
            } else {
                this.state.policeApiError = result?.error || "لم يتم العثور على البيانات";
                this.state.policeDataFound = false;
            }
        } catch (e) {
            console.error("ROP error:", e);
            console.error("ROP error details:", {
                message: e.message,
                stack: e.stack,
                name: e.name
            });
            this.state.policeApiError = "خطأ في الاتصال بقاعدة بيانات الشرطة";
            this.state.policeDataFound = false;
        } finally {
            this.state.isPoliceApiLoading = false;
            this.render?.();
        }
    };
}
