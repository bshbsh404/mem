/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class GroupReservations extends Component {
    setup() {
        this.rpc = useService("rpc");
        
        // References for form fields
        this.inputCompanyNameRef = useRef("inputCompanyName");
        this.inputHostingEmployeeRef = useRef("inputHostingEmployee");
        this.inputVisitDateRef = useRef("inputVisitDate");
        this.inputVisitTimeRef = useRef("inputVisitTime");
        
        this.state = useState({
            errorMessage: null,
            visitors: [],
            nextVisitorId: 1
        });
    }
    
    _addVisitor() {
        const newVisitor = {
            id: this.state.nextVisitorId++,
            name: '',
            email: '',
            phone: '',
            idNumber: '',
            employeeEmail: ''
        };
        this.state.visitors.push(newVisitor);
    }
    
    _removeVisitor(event) {
        const visitorId = parseInt(event.target.closest('button').getAttribute('data-visitor-id'));
        this.state.visitors = this.state.visitors.filter(visitor => visitor.id !== visitorId);
    }
    
    _onVisitorFieldChange(event) {
        const visitorId = parseInt(event.target.getAttribute('data-visitor-id'));
        const fieldClass = event.target.className;
        const value = event.target.value;
        
        const visitor = this.state.visitors.find(v => v.id === visitorId);
        if (!visitor) return;
        
        if (fieldClass.includes('visitor-name')) {
            visitor.name = value;
        } else if (fieldClass.includes('visitor-email')) {
            visitor.email = value;
        } else if (fieldClass.includes('visitor-phone')) {
            visitor.phone = value;
        } else if (fieldClass.includes('visitor-id-number')) {
            visitor.idNumber = value;
        } else if (fieldClass.includes('visitor-employee-email')) {
            visitor.employeeEmail = value;
        }
    }
    
    async _onSubmit() {
        // Clear previous error messages
        this.state.errorMessage = null;
        
        // Validate form data
        if (this.state.visitors.length === 0) {
            this.state.errorMessage = "Please add at least one visitor.";
            return;
        }
        
        const companyName = this.inputCompanyNameRef.el.value;
        const hostingEmployee = this.inputHostingEmployeeRef.el.value;
        const visitDate = this.inputVisitDateRef.el.value;
        const visitTime = this.inputVisitTimeRef.el.value;
        
        if (!companyName || !hostingEmployee || !visitDate || !visitTime) {
            this.state.errorMessage = "Please fill in all required reservation details.";
            return;
        }
        
        // Validate each visitor
        for (const visitor of this.state.visitors) {
            if (!visitor.name || !visitor.email || !visitor.phone || !visitor.idNumber) {
                this.state.errorMessage = "Please fill in all required fields for all visitors.";
                return;
            }
        }
        
        try {
            // Submit group reservation
            const reservationData = {
                company_name: companyName,
                hosting_employee: hostingEmployee,
                visit_date: visitDate,
                visit_time: visitTime,
                visitors: this.state.visitors.map(visitor => ({
                    name: visitor.name,
                    email: visitor.email,
                    phone: visitor.phone,
                    id_number: visitor.idNumber,
                    employee_email: visitor.employeeEmail || false
                })),
                station_id: this.props.stationInfo.id
            };
            
            const result = await this.rpc("/frontdesk/submit_group_reservation", reservationData);
            
            if (result.success) {
                // Show success message and reset form
                alert("Group reservation submitted successfully!");
                this._resetForm();
            } else {
                this.state.errorMessage = result.error || "Failed to submit group reservation.";
            }
        } catch (error) {
            console.error("Error submitting group reservation:", error);
            this.state.errorMessage = "An error occurred while submitting the reservation.";
        }
    }
    
    _resetForm() {
        this.inputCompanyNameRef.el.value = '';
        this.inputHostingEmployeeRef.el.value = '';
        this.inputVisitDateRef.el.value = '';
        this.inputVisitTimeRef.el.value = '';
        this.state.visitors = [];
        this.state.nextVisitorId = 1;
        this.state.errorMessage = null;
    }
}

GroupReservations.template = "frontdesk.GroupReservations";
GroupReservations.props = {
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
    frontdeskUrl: String,
};

registry.category("frontdesk_screens").add("GroupReservations", GroupReservations);
