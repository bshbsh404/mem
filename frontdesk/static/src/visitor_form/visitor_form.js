/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef, useState} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class VisitorForm extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.inputNameRef = useRef("inputName");
        this.inputSecondNameRef = useRef("inputSecondName");
        this.inputThirdNameRef = useRef("inputThirdName");
        this.inputFourthNameRef = useRef("inputFourthName");
        this.inputPhoneRef = useRef("inputPhone");
        this.inputLandlineRef = useRef("inputLandline");
        this.inputEmailRef = useRef("inputEmail");
        this.inputCompanyRef = useRef("inputCompany");
        this.inputVisitorIDRef = useRef("inputVisitorID");
        this.inputPassportRef = useRef("inputPassport");
        this.inputEmpIDRef = useRef("inputEmpID");

        this.props.updatePlannedVisitors();
        this.state = useState({
            showPhoneError: false,
            visitorType: 'individual',  // Default visitor type
            selectedIDType: 'visitorID',  // Default selected ID type
            visitorName: this.props.visitorData.visitorName || "",
            visitorSecondName: this.props.visitorData.visitorSecondName || "",
            visitorThirdName: this.props.visitorData.visitorThirdName || "",
            visitorFourthName: this.props.visitorData.visitorFourthName || "",
            visitorPhone: this.props.visitorData.visitorPhone || "",
            visitorLandline: this.props.visitorData.visitorLandline || "",
            visitorEmail: this.props.visitorData.visitorEmail || "",
            visitorCompany: this.props.visitorData.visitorCompany || "",
            visitorID: this.props.visitorData.visitorID || "",
            passport: this.props.visitorData.passport || "",
        });
        // onMounted(() => {
            // this.inputNameRef.el.focus();
        // });
        // onMounted(() => {
        //     setTimeout(() => {
        //         this._loadRecaptchaSiteKey();
        //     }, 100);
        // });
        onWillUnmount(() => {
            this.props.clearUpdatePlannedVisitors();
        });
    }

    async _onInputEmpIDChange(event) {
        const empID = event.target.value;
        if (!empID) return;

        try {
            const result = await this.rpc("/frontdesk/get_employee_info", { emp_id: empID });
            if (result && !result.error) {
                this.inputNameRef.el.value = result.name || "";
                if (this.inputSecondNameRef.el) {
                    this.inputSecondNameRef.el.value = result.second_name || "";
                }
                if (this.inputThirdNameRef.el) {
                    this.inputThirdNameRef.el.value = result.third_name || "";
                }
                if (this.inputFourthNameRef.el) {
                    this.inputFourthNameRef.el.value = result.fourth_name || "";
                }

                if(this.inputSecondNameRef.el == null && this.inputThirdNameRef.el != null){
                    this.inputThirdNameRef.el.value = result.second_name || "";
                }else if(this.inputSecondNameRef.el == null && this.inputThirdNameRef.el == null){
                    this.inputFourthNameRef.el.value = result.second_name || "";
                }

                // if identification_id is set, then set it to inputVisitorIDRef
                try{
                    if (result.identification_id) {
                    this.inputVisitorIDRef.el.value = result.identification_id;
                    } else {
                        this.inputVisitorIDRef.el.value = "";
                        try{
                            // if passport is set, then set it to inputPassportRef
                            if (result.passport_id) {
                                this.inputPassportRef.el.value = result.passport_id;
                            } else {
                                this.inputPassportRef.el.value = "";
                            }
                        }  catch (error) {
                            console.error("Error setting passport_id");
                        }
                    }
                }  catch (error) {
                    console.error("Error setting identification_id");
                }
                
            } else {
                console.warn("Employee not found");
            }
        } catch (err) {
            console.warn("RPC error:", err);
            console.error("Failed to fetch employee info");
        }
    }


    /**
     * This method handles the change of visitor type (Individual, Company, Employee)
     * @private
     */
    _onVisitorTypeChange(event) {
        this.state.visitorType = event.target.value;

        // Reset the relevant fields when the visitor type changes
        // this.inputEmailRef.el?.value = "";
        // this.inputCompanyRef.el?.value = "";
        // this.inputEmpIDRef.el?.value = "";
        // this.inputVisitorIDRef.el?.value = "";
        // this.inputPassportRef.el?.value = "";

        if (this.state.visitorType === 'employee') {
            // Clear fields specific to other types
            // this.inputEmailRef.el.required = false;
            // this.inputCompanyRef.el.required = false;
            // this.inputVisitorIDRef.el.required = false;
            // this.inputPassportRef.el.required = false;
        } else if (this.state.visitorType === 'company') {
            // Make company name field mandatory
            // this.inputCompanyRef.el.required = true;
        }
    }

    /**
     * This method handles the change of identification type (Visitor ID or Passport)
     * @private
     */
    _onIDTypeChange(event) {
        this.state.selectedIDType = event.target.value;
    }

    async _loadRecaptchaSiteKey() {
        try {
            const result = await this.rpc(`/frontdesk/get_recaptcha`, {});
            // if the result is not empty, then set the recaptcha site key
            if (result) {
                // set the recaptcha site key to .g-recaptcha
                document.querySelector(".g-recaptcha").setAttribute("data-sitekey", result);
            }
        } catch (error) {
        }
    }

    /**
     * @private
     */
    _onSubmit() {

        // check if recaptcha is filled
        console.log("inside _onSubmit");
        console.log("currentLang", this.props.currentLang);
        // check if .g-recaptcha-response exists
        if (document.querySelector(".g-recaptcha-response")) {
            const recaptcha = document.querySelector(".g-recaptcha-response").value;
            if (!recaptcha) {
                const recaptchaElement = document.querySelector(".g-recaptcha");
                recaptchaElement.style.border = "1px solid red";
                recaptchaElement.style.borderRadius = "5px";
                recaptchaElement.style.padding = "5px";
                recaptchaElement.style.boxShadow = "0 0 5px red";
                setTimeout(() => {
                    recaptchaElement.style.border = "";
                    recaptchaElement.style.borderRadius = "";
                    recaptchaElement.style.padding = "";
                    recaptchaElement.style.boxShadow = "";
                }, 3000);
                return;
            }
        }

        const phoneValue = this.inputPhoneRef.el?.value || "";
        if (phoneValue && !(phoneValue.startsWith("7") || phoneValue.startsWith("9") || phoneValue.startsWith("00") || phoneValue.startsWith("+"))) {
            this.state.showPhoneError = true;
        }else{
            console.log("this.inputVisitorIDRef.el?.value", this.inputVisitorIDRef.el?.value);
            this.state.showPhoneError = false;

            if (this.state.visitorType === 'company') {
                this.props.setVisitorData(
                    this.inputNameRef.el?.value || false,
                    this.inputSecondNameRef.el?.value || false,
                    this.inputThirdNameRef.el?.value || false,
                    this.inputFourthNameRef.el?.value || false,
                    this.inputPhoneRef.el?.value || false,
                    this.inputLandlineRef.el?.value || false,
                    this.inputEmailRef.el?.value || false,
                    this.inputCompanyRef.el?.value || false,
                    this.inputVisitorIDRef.el?.value || false,
                    this.inputPassportRef.el?.value || false,
                    false,
                );
            } else if (this.state.visitorType === 'individual') {
                this.props.setVisitorData(
                    this.inputNameRef.el?.value || false,
                    this.inputSecondNameRef.el?.value || false,
                    this.inputThirdNameRef.el?.value || false,
                    this.inputFourthNameRef.el?.value || false,
                    this.inputPhoneRef.el?.value || false,
                    this.inputLandlineRef.el?.value || false,
                    this.inputEmailRef.el?.value || false,
                    false,
                    this.inputVisitorIDRef.el?.value || false,
                    this.inputPassportRef.el?.value || false,
                    false,
                );
            } else if (this.state.visitorType === 'employee') {
                this.props.setVisitorData(
                    this.inputNameRef.el?.value || false,
                    this.inputSecondNameRef.el?.value || false,
                    this.inputThirdNameRef.el?.value || false,
                    this.inputFourthNameRef.el?.value || false,
                    false,
                    false,
                    false,
                    false,
                    this.inputVisitorIDRef.el?.value || false,
                    this.inputPassportRef.el?.value || false,
                    this.inputEmpIDRef.el?.value || false,
                );
            }

            

            if (this.state.visitorType !== 'employee') {
                this.props.showScreen("HostPage");
            }else{
                this.props.showScreen("RegisterPage");
            }
        }
    }
    
   
}

VisitorForm.template = "frontdesk.VisitorForm";
VisitorForm.props = {
    clearUpdatePlannedVisitors: Function,
    currentComponent: String,
    currentLang: String,
    isMobile: Boolean,
    isPlannedVisitors: Boolean,
    langs: [Object, Boolean],
    onChangeLang: Function,
    setVisitorData: Function,
    showScreen: Function,
    stationInfo: Object,
    updatePlannedVisitors: Function,
    visitorData: [Object, Boolean],
    theme: String,
};

registry.category("frontdesk_screens").add("VisitorForm", VisitorForm);
