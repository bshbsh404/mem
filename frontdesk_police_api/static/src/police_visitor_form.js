/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useRef, useState} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class PoliceVisitorForm extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.inputNameRef = useRef("inputName");
        this.inputFourthNameRef = useRef("inputFourthName");
        this.inputPhoneRef = useRef("inputPhone");
        this.inputEmailRef = useRef("inputEmail");
        this.inputPoliceCivilIDRef = useRef("inputPoliceCivilID");
        this.inputCardExpiryRef = useRef("inputCardExpiry");

        this.state = useState({
            isPoliceApiLoading: false,
            policeApiError: null,
            policeDataFound: false,
            visitorName: "",
            visitorFourthName: "",
            visitorPhone: "",
            visitorEmail: "",
        });
    }

    /**
     * البحث في قاعدة بيانات الشرطة العمانية (ROP)
     */
    async _onPoliceIdLookup() {
        const civilId = this.inputPoliceCivilIDRef.el?.value;
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
            console.log("البحث في قاعدة بيانات الشرطة العمانية عن:", civilId);
            
            const result = await this.rpc("/frontdesk/police_api/get_visitor_data", {
                civil_id: civilId,
                card_expiry: cardExpiry,
                context: {
                    lang: this.env.lang || 'ar' // إرسال لغة الواجهة الحالية
                }
            });

            console.log("=== استجابة API الشرطة ===");
            console.log("result:", result);
            console.log("result.success:", result.success);
            console.log("result.data:", result.data);

            if (result.success && result.data) {
                console.log("تم استرجاع البيانات بنجاح:", result.data);
                
                // تمرير البيانات كاملة إلى دالة الملء
                this._fillVisitorDataFromPolice(result.data);
                this.state.policeDataFound = true;
                this.state.policeApiError = null;
            } else {
                this.state.policeApiError = result.error || "لم يتم العثور على البيانات";
                this.state.policeDataFound = false;
            }

        } catch (error) {
            console.error("خطأ في API الشرطة:", error);
            this.state.policeApiError = "خطأ في الاتصال بقاعدة بيانات الشرطة";
            this.state.policeDataFound = false;
        } finally {
            this.state.isPoliceApiLoading = false;
        }
    }

    /**
     * ملء البيانات من API الشرطة
     */
    _fillVisitorDataFromPolice(data) {
        console.log("=== ملء البيانات من API الشرطة ===");
        console.log("data type:", typeof data);
        console.log("data:", data);
        
        let firstName = "";
        let familyName = "";
        let email = "";
        let phone = "";
        
        if (data && typeof data === 'string') {
            console.log("معالجة البيانات كـ string");
            // في حال كانت نص XML — يمكن تترك أو تحذف هذا الفرع إذا متأكد أن البيانات دائماً object
        } else if (data && typeof data === 'object') {
            console.log("معالجة البيانات كـ object");
            console.log("لغة البيانات:", data.language);
            
            // استخدام البيانات حسب اللغة المطلوبة
            firstName = data.name || "";
            familyName = data.fourth_name || "";
            phone = data.phone || "";
            email = data.email || "";
        }
        
        console.log("=== البيانات المستخرجة ===");
        console.log("firstName:", firstName);
        console.log("familyName:", familyName);
        console.log("phone:", phone);
        console.log("email:", email);
        
        if (firstName) {
            this.state.visitorName = firstName;
            if (this.inputNameRef.el) {
                this.inputNameRef.el.value = firstName;
                console.log("تم تحديث الاسم الأول في الحقل");
            }
        }
        
        if (familyName) {
            this.state.visitorFourthName = familyName;
            if (this.inputFourthNameRef.el) {
                this.inputFourthNameRef.el.value = familyName;
                console.log("تم تحديث اسم العائلة في الحقل");
            }
        }
        
        if (email) {
            this.state.visitorEmail = email;
            if (this.inputEmailRef.el) {
                this.inputEmailRef.el.value = email;
                console.log("تم تحديث البريد الإلكتروني في الحقل");
            }
        }
        
        if (phone) {
            this.state.visitorPhone = phone;
            if (this.inputPhoneRef.el) {
                this.inputPhoneRef.el.value = phone;
                console.log("تم تحديث رقم الهاتف في الحقل");
            }
        }
        
        console.log("=== تم ملء البيانات بنجاح ===");
        console.log("state.visitorName:", this.state.visitorName);
        console.log("state.visitorFourthName:", this.state.visitorFourthName);
        console.log("state.visitorPhone:", this.state.visitorPhone);
        console.log("state.visitorEmail:", this.state.visitorEmail);
    }

    /**
     * إرسال النموذج
     */
    _onSubmit() {
        console.log("إرسال نموذج الشرطة");
        
        // التحقق من الحقول المطلوبة
        const name = this.inputNameRef.el?.value;
        const familyName = this.inputFourthNameRef.el?.value;
        const email = this.inputEmailRef.el?.value;
        const phone = this.inputPhoneRef.el?.value;
        
        if (!name || !familyName || !email || !phone) {
            alert("يرجى ملء جميع الحقول المطلوبة");
            return;
        }
        
        // إرسال البيانات
        this.props.setVisitorData(
            name,
            false, // second name
            false, // third name
            familyName,
            phone,
            false, // landline
            email,
            false, // company
            false, // visitor ID
            false, // passport
            false, // employee ID
        );
        
        // الانتقال إلى الصفحة التالية
        this.props.showScreen("HostPage");
    }
}

PoliceVisitorForm.template = "frontdesk.PoliceVisitorForm";
PoliceVisitorForm.props = {
    setVisitorData: Function,
    showScreen: Function,
    theme: String,
};

registry.category("frontdesk_screens").add("PoliceVisitorForm", PoliceVisitorForm);
