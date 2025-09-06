/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useRef, useState,onMounted, onWillUnmount } from "@odoo/owl";
import { Many2One } from "./many2one/many2one";
import { useService } from "@web/core/utils/hooks";

export class HostPage extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.buttonRef = useRef("button");
        this.checkRef = useRef("check");

        this.state = useState({
            selectedPurpose: null,
            departmentFilter: [],
            holidays: [],
            errorMessage: null, // For storing the error message
            isRecurring: false,
            visitType: "employee", // New state for visit type, default is 'employee'
        });

        onMounted(() => {
            this._loadHolidays();
            // setTimeout(() => {
            //     this._loadRecaptchaSiteKey();
            // }, 100);
        });

    }

    _onVisitTypeChange(event) {
        this.state.visitType = event.target.value;
        // Reset fields if switching between types
        if (this.state.visitType === "employee") {
            this.state.selectedState = null; // Reset state if switching to employee
        }
    }

    async _loadHolidays() {
        try {
            const result = await this.rpc(`/frontdesk/${this.props.stationId}/${this.props.token}/get_holidays`, {});
            this.state.holidays = result;
        } catch (error) {
        }
    }

    async _loadRecaptchaSiteKey() {
        try {
            const result = await this.rpc(`/frontdesk/get_recaptcha`, {});
            if (result) {
                // set the recaptcha site key to .g-recaptcha
                document.querySelector(".g-recaptcha").setAttribute("data-sitekey", result);
            }
        } catch (error) {
        }
    }

    _isHoliday(date) {
        const selectedDate = new Date(date);
        for (const holiday of this.state.holidays) {
            const dateFrom = new Date(holiday.date_from);
            const dateTo = new Date(holiday.date_to);
            if (selectedDate >= dateFrom && selectedDate <= dateTo) {
                return true;
            }
        }
        return false;
    }

    _isOutsideWorkingHours(time) {
        const [hours, minutes] = time.split(':').map(Number);  // Split "22:30" into hours and minutes
        const selectedTime = new Date();
        selectedTime.setHours(hours, minutes, 0, 0);  // Set the hours and minutes to the selected time
    
        const startTime = new Date();
        startTime.setHours(this.props.stationInfo.working_hours_start, 0, 0, 0);  // Set working start time
    
        const endTime = new Date();
        endTime.setHours(this.props.stationInfo.working_hours_end, 0, 0, 0);  // Set working end time

        console.log('Selected time:', selectedTime);
        console.log('Start time:', startTime);
        console.log('End time:', endTime);
        console.log(selectedTime >= startTime && selectedTime <= endTime);
    
        return selectedTime >= startTime && selectedTime <= endTime;
    }
    

    /**
     * This method handles the change of identification type (Visitor ID or Passport)
     * @private
     */
    _onRecurringChange(event) {
        if(document.getElementById('is_recurring').checked == true){
            this.state.isRecurring = "on";
        }else{
            this.state.isRecurring = "off";
        }
        console.log('Recurring:', this.state.isRecurring);
    }


    /**
     * This method disables the confirm button.
     * When the text in the input field is not present in the selection.
     *
     * @param {Boolean} isDisable
     */
    disableButton(isDisable) {
        this.buttonRef.el.disabled = isDisable;
    }

    _onCheck() {
        var check = this.checkRef.el.value;
        this.buttonRef.el.disabled = check !== "on";
    }

    /**
     * This method is triggered when the confirm button is clicked.
     * It sets the host data and displays the RegisterPage component.
     *
     * @private
     */
    async _onConfirm() { 
        // check if recaptcha is filled
        if (document.querySelector(".g-recaptcha-response")) {
            const recaptcha = document.querySelector(".g-recaptcha-response").value;
            if (!recaptcha) {
                // alert("Please fill the recaptcha");
                // just add a style to the recaptcha
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

        // Clear any previous error messages
        this.state.errorMessage = null;

        if ($('#is_recurring').length) {
            var is_recurring = $('#is_recurring').val();
        } else {
            var is_recurring = '';
        }
        if ($('#planned_date').length) {
            var planned_date = $('#planned_date').val();
        } else {
            var planned_date = '';
        }
        if ($('#planned_date_end').length) {
            var planned_date_end = $('#planned_date_end').val();
        } else {
            var planned_date_end = '';
        }
        if (this._isHoliday(planned_date)) {
            this.state.errorMessage = "The selected date falls within a holiday period and cannot be selected.";
            setTimeout(() => {
                const errorElement = document.getElementById("errorMessage");
                if (errorElement) {
                    errorElement.scrollIntoView({ behavior: 'smooth' });
                }
            }, 100);
            return;
        }


        

        if ($('#phone').length) {
            var phone = $('#phone').val();
        } else {
            var phone = '';
        }

        if ($('#email').length) {
            var email = $('#email').val();
            // check if email contains a domain, remove it and keep the part before the @
            if (email.includes('@')){
                email = email.split('@')[0];
            }
            
        } else {
            var email = '';
        }

        if ($('#name').length) {
            var name = $('#name').val();
        } else {
            var name = '';
        }

        

        if ($('#planned_time').length) {
            var planned_time = $('#planned_time').val();
        } else {
            var planned_time = '';
        }

        // check if is between working_hours_start and working_hours_end
        if(!this._isOutsideWorkingHours(planned_time)){
            this.state.errorMessage = "The selected time is outside the working hours.";
            setTimeout(() => {
                const errorElement = document.getElementById("errorMessage");
                if (errorElement) {
                    errorElement.scrollIntoView({ behavior: 'smooth' });
                }
            }, 100);
            return
        }

        console.log("planned_date", planned_date);
        if (planned_date === new Date().toISOString().split('T')[0]) {
            const now = new Date();
            const planned = new Date();
            if (planned_time === '' || planned_time === null) {
                this.state.errorMessage = "Please select a planned time.";
                setTimeout(() => {
                    const errorElement = document.getElementById("errorMessage");
                    if (errorElement) {
                        errorElement.scrollIntoView({ behavior: 'smooth' });
                    }
                }, 100);
                return;
            }
            const [hours, minutes] = planned_time.split(':').map(Number);
            planned.setHours(hours, minutes, 0, 0);
        
            // const buffer = new Date(now.getTime() + 5 * 60000); // now + 5 mins
        
            // if (planned <= buffer) {
            //     this.state.errorMessage = "Planned time must be at least 5 minutes from now.";
            //     setTimeout(() => {
            //         const errorElement = document.getElementById("errorMessage");
            //         if (errorElement) {
            //             errorElement.scrollIntoView({ behavior: 'smooth' });
            //         }
            //     }, 100);
            //     return;
            // }
        }

        
        if ($('#landline').length) {
            var landline = $('#landline').val();
        } else {
            var landline = '';
        }

        var purpose = this.purpose;

        

        console.log("purpose final");
        var other_reason = '';
        if(purpose == null){
            const visitPurposeInput = document.querySelector('#visit_purpose');
            const visitOtherPurposeInput = document.querySelector('#other_reason');
            if(visitOtherPurposeInput){
                other_reason = visitOtherPurposeInput.value;
            }
            if(visitPurposeInput){
                purpose = visitPurposeInput.value;
            }
        }

        console.log(purpose);
        var visit_type = false;
        var wilayat = false;
        try{
            visit_type = document.querySelector('input[name="visitType"]:checked').value; 
        }catch(e){
            console.log(e);
        }

        try{
            wilayat = document.querySelector('#wilayat').value;
        }catch(e){
            console.log(e);
        }
        console.log("_onConfirm visit_type", visit_type);
        console.log("_onConfirm wilayat", wilayat);
        if(purpose == null || purpose == ''){
            this.state.errorMessage = "Please select a purpose for the visit.";
            setTimeout(() => {
                const errorElement = document.getElementById("errorMessage");
                if (errorElement) {
                    errorElement.scrollIntoView({ behavior: 'smooth' });
                }
            }, 100);
            return;
        }
        if(visit_type == "department"){
            // get the value of department
            var selected_department = $('#department').val();
            if(selected_department == '' || selected_department == null){
                this.state.errorMessage = "Please select a department.";
                setTimeout(() => {
                    const errorElement = document.getElementById("errorMessage");
                    if (errorElement) {
                        errorElement.scrollIntoView({ behavior: 'smooth' });
                    }
                }, 100);
                return;
            }
        }

        // var recaptcha_response = document.querySelector(".g-recaptcha-response").value;
        if (document.querySelector(".g-recaptcha-response")) {
            var recaptcha_response = grecaptcha.getResponse();
        }else{
            var recaptcha_response = '';
        }

        // Validate reCAPTCHA on the backend
        // try {
        //     const validationResponse = await this.rpc('/frontdesk/validate_recaptcha', { recaptcha_response: recaptcha_response });
        //     if (!validationResponse.success) {
        //         alert(validationResponse.message || "reCAPTCHA validation failed. Please try again.");
        //         return;
        //     }
        // } catch (error) {
        //     console.error("Error during reCAPTCHA validation:", error);
        //     alert("An error occurred while validating reCAPTCHA. Please try again.");
        //     return;
        // }
        // can we print currentLang here?
        console.log("currentLang", this.currentLang);

        this.props.setHostData(this.host, name, phone, email, is_recurring, planned_date, planned_date_end, planned_time, 60, purpose, other_reason, landline, visit_type, wilayat, recaptcha_response, this.props.currentLang);
        this.props.showScreen("RegisterPage");
    }

    /**
     * @param {Object} host
     */
    selectedHost(host) {
        this.host = host;
    }

    /**
     * @param {Object} purpose
     */
    async selectedPurpose(purpose) {
        this.purpose = purpose;
    }
}

HostPage.template = "frontdesk.HostPage";
HostPage.components = { Many2One };
HostPage.props = {
    setHostData: Function,
    showScreen: Function,
    stationId: Number,
    stationInfo: Object,
    token: String,
    theme: String,
};

registry.category("frontdesk_screens").add("HostPage", HostPage);
