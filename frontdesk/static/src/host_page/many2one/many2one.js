/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { Component, useState } from "@odoo/owl";

export class Many2One extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            selectedPurpose: null,
            selectedDepartment: null,
            selectedEmployee: null,
            filteredDepartments: [],
            showOtherPurposeInput: false,  // Track if 'Other' is selected
            otherPurpose: "",  // Store the custom 'Other' purpose
            otherReasons: [],  // List of other reasons
            selectedOtherReason: null,  // Selected "Other Reason"
            
            showWilayatInput: false,  // Track if 'Other' is selected
            showDepartmentInput: false,
            showEmployeeInput: false,  // Track if employee field should be shown
            wilayatOptions: [], // List of Wilayat options
            selectedWilayat: null, // For storing the selected Wilayat
        });
    }

    async loadPurposeOptions(request) {
        console.log("loadPurposeOptions");
        if (this.lastPurposesProm) {
            this.lastPurposesProm.abort(false);
        }
        this.lastPurposesProm = this.purposeSearch(request);
        const purposesRecords = await this.lastPurposesProm;
        if (!purposesRecords.length) {
            this.props.disableButton(true);
        }
        console.log(purposesRecords);

        return purposesRecords.map((result) => this.mapPurposeRecordToOption(result));
    }

    mapPurposeRecordToOption(result) {
        return {
            value: result[0],
            label: result[1].split("\n")[0],
            displayName: result[1],
            is_other: result[2],
        };
    }

    purposeSearch(name) {
        const urlParams = new URLSearchParams(window.location.search);
        const lang = urlParams.get('lang');
        return this.rpc(`/frontdesk/${this.props.stationId}/${this.props.token}/${lang}/get_purposes`, {
            name: name,
        });
    }

    async loadDepartmentOptions(request) {
        console.log("loadDepartmentOptions");
        if (!this.state.selectedPurpose) {
            return [];
        }
        if (this.lastDepartmentsProm) {
            this.lastDepartmentsProm.abort(false);
        }
        this.lastDepartmentsProm = this.departmentSearch(request);
        const departmentsRecords = await this.lastDepartmentsProm;
        if (!departmentsRecords.length) {
            this.props.disableButton(true);
        }
        console.log(departmentsRecords);

        return departmentsRecords.map((result) => this.mapRecordToOption(result));
    }

    departmentSearch(name) {
        const urlParams = new URLSearchParams(window.location.search);
        const lang = urlParams.get('lang');
        return this.rpc(`/frontdesk/${this.props.stationId}/${this.props.token}/${lang}/get_hosts`, {
            name: name,
            purpose_id: this.state.selectedPurpose.id,
        });
    }

    async loadEmployeeOptions(request) {
        console.log("loadEmployeeOptions");
        if (!this.state.selectedPurpose) {
            return [];
        }
        if (this.lastEmployeesProm) {
            this.lastEmployeesProm.abort(false);
        }
        this.lastEmployeesProm = this.employeeSearch(request);
        const employeesRecords = await this.lastEmployeesProm;
        console.log("Employees:", employeesRecords);

        return employeesRecords.map((result) => this.mapEmployeeRecordToOption(result));
    }

    employeeSearch(name) {
        const urlParams = new URLSearchParams(window.location.search);
        const lang = urlParams.get('lang');
        return this.rpc(`/frontdesk/${this.props.stationId}/${this.props.token}/${lang}/get_employees`, {
            name: name,
            purpose_id: this.state.selectedPurpose.id,
        });
    }

    mapEmployeeRecordToOption(result) {
        return {
            value: result[0],
            label: result[1].split("\n")[0],
            displayName: result[1],
            work_email: result[2],
            mobile_phone: result[3],
            work_phone: result[4],
        };
    }

    mapRecordToOption(result) {
        return {
            value: result[0],
            label: result[1].split("\n")[0],
            displayName: result[1],
        };
    }

    async onPurposeSelect(option, params = {}) {
        const purpose = {
            id: option.value,
            display_name: option.displayName,
            is_other: option.is_other,
            state_ids: option.state_ids,
        };
        this.state.showEmployeeInput = false; // Reset employee input visibility
        this.state.selectedEmployee = null; // Reset selected employee

        console.log("onPurposeSelect this purpose");
        console.log(option.value);
        console.log(option.displayName);
        console.log(option.state_ids);
        // Reload departments if necessary
        if (this.state.selectedPurpose?.id !== purpose.id) {
            this.state.selectedPurpose = purpose;
            // Reload departments only if a different purpose is selected
            this.state.filteredDepartments = await this.loadDepartmentOptions("");
        }
        this.props.update(purpose);
        

        // Check if the selected purpose has is_other set to true
        if (purpose.is_other) {
            this.state.showOtherPurposeInput = true;  // Show the custom purpose input field
            await this.loadOtherReasons();  // Load other reasons
        } else {
            this.state.showOtherPurposeInput = false;  // Hide the custom purpose input field
            this.state.otherPurpose = "";  // Reset the custom purpose
            this.state.otherReasons = [];
            this.state.selectedOtherReason = null;
        }

        // Load states from the selected purpose
        // if (purpose.state_ids && purpose.state_ids.length) {
        //     this.state.stateOptions = purpose.state_ids.map(state => ({
        //         id: state.id,
        //         name: state.name,
        //     }));
        // } else {
        //     this.state.stateOptions = [];
        // }
        // Update the selected purpose
        // this.state.selectedPurpose = purpose;
        // this.props.update(purpose);
    
        // Update the visit purpose input field
        const visitPurposeInput = document.querySelector('#visit_purpose');
        visitPurposeInput.value = option.displayName;
        if(visitPurposeInput.value != option.displayName){
            visitPurposeInput.value = option.displayName;
        }

        // handle wilayat
        console.log("this.props.stationInfo.is_online", this.props.isOnline);
        // get the value of checkbox visitType
        if(this.props.isOnline){
            console.log("online");
            var visitType = document.querySelector('input[name="visitType"]:checked').value;
            console.log("visitType", visitType);
            if(visitType && visitType == "department"){
                this.state.showWilayatInput = true;
                this.state.showDepartmentInput = true;
                await this.loadWilayat(option.value);
            }else{
                this.state.showWilayatInput = false;
                this.state.showDepartmentInput = false;
                this.state.wilayatOptions = [];
                this.state.selectedWilayat = null;
            }
        }else{
            console.log("not online");
            this.state.showWilayatInput = false;
            this.state.wilayatOptions = [];
            this.state.selectedWilayat = null;
            var visitType = document.querySelector('input[name="visitType"]:checked').value;
            if(visitType && visitType == "department"){
                this.state.showDepartmentInput = true;
            }else{
                this.state.showDepartmentInput = false;
            }
        }

        const visitTypeElement = document.querySelector('input[name="visitType"]:checked');
        if (visitTypeElement && visitTypeElement.value === 'employee') {
            this.state.showEmployeeInput = true;
        }
    }

    onDepartmentSelect(option, params = {}) {
        const department = {
            id: option.value,
            display_name: option.displayName,
        };
        this.state.selectedDepartment = department;

        if (department) {
            this.props.disableButton(false);
        }
        this.props.update(department);
        // params.input.value = option.displayName;

        // update the visit purpose input field
        const departmentInput = document.querySelector('#department');
        if (departmentInput) {
            departmentInput.value = option.displayName;
        }
    }

    onEmployeeSelect(option, params = {}) {
        const employee = {
            id: option.value,
            display_name: option.displayName,
            work_email: option.work_email,
            mobile_phone: option.mobile_phone,
            work_phone: option.work_phone,
        };
        
        this.state.selectedEmployee = employee;
        
        // Clear and populate the employee form fields
        this.clearAndPopulateEmployeeFields(employee);
        
        this.props.update(employee);

        // update the employee input field
        const employeeInput = document.querySelector('#employee');
        if (employeeInput) {
            employeeInput.value = option.displayName;
        }
    }

    clearAndPopulateEmployeeFields(employee) {
        // Clear existing values
        const nameInput = document.querySelector('#name');
        const phoneInput = document.querySelector('#phone');
        const emailInput = document.querySelector('#email');
        
        if (nameInput) {
            nameInput.value = employee.display_name || '';
        }
        
        if (phoneInput) {
            phoneInput.value = employee.mobile_phone || employee.work_phone || '';
        }
        
        if (emailInput && employee.work_email) {
            // Extract only the part before @ from email
            const emailPart = employee.work_email.includes('@') 
                ? employee.work_email.split('@')[0] 
                : employee.work_email;
            emailInput.value = emailPart;
        }
    }

    async loadOtherReasons() {
        // Fetch "Other Reasons" using RPC
        const reasons = await this.rpc('/frontdesk/get_other_reasons', {});
        this.state.otherReasons = reasons.map(reason => ({
            id: reason.id,
            name: reason.name,
        }));
    }

    async loadWilayat(purpose_id) {
        // Fetch "Wilayat" using RPC
        console.log("loadWilayat");
        console.log(purpose_id);
        const wilayat = await this.rpc('/frontdesk/get_wilayat', {
            'purpose_id': purpose_id,
        });
        this.state.wilayatOptions = wilayat.map(reason => ({
            id: reason.id,
            name: reason.name,
        }));
        if(this.state.wilayatOptions && this.state.wilayatOptions.length > 0){
            this.state.showWilayatInput = true;
        }else{
            this.state.showWilayatInput = false;
        }
    }

    onOtherReasonSelect(reason) {
        this.state.selectedOtherReason = reason;
        this.props.update(reason);
    }

    get purposeSources() {
        return [{
            placeholder: _t("Loading..."),
            options: this.loadPurposeOptions.bind(this),
            optionTemplate: "avatarAutoComplete",
        }];
    }

    get departmentSources() {
        return [{
            placeholder: _t("Loading..."),
            options: this.loadDepartmentOptions.bind(this),
            optionTemplate: "avatarAutoComplete",
        }];
    }

    get employeeSources() {
        return [{
            placeholder: _t("Loading..."),
            options: this.loadEmployeeOptions.bind(this),
            optionTemplate: "avatarAutoComplete",
        }];
    }
}

Many2One.template = "frontdesk.Many2One";
Many2One.components = { AutoComplete };
Many2One.props = {
    disableButton: Function,
    stationId: Number,
    token: String,
    update: Function,
    isOnline: Boolean,
    visitType: String,
};
