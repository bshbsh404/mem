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
        this.inputHostingEmployeeSearchRef = useRef("inputHostingEmployeeSearch");
        this.inputVisitDateRef = useRef("inputVisitDate");
        this.inputVisitTimeRef = useRef("inputVisitTime");
        
        this.state = useState({
            errorMessage: null,
            visitors: [],
            nextVisitorId: 1,
            employees: [],
            filteredEmployees: [],
            showEmployeeDropdown: false,
            employeeSearchQuery: '',
            selectedEmployeeId: null,
            selectedEmployeeName: ''
        });
        
        // Load employees on component mount
        this._loadEmployees();
    }
    
    async _loadEmployees() {
        try {
            const response = await this.rpc("/frontdesk/get_all_employees", {});
            if (response && response.employees) {
                this.state.employees = response.employees;
                this.state.filteredEmployees = response.employees;
            }
        } catch (error) {
            console.error("Error loading employees:", error);
            this.state.errorMessage = "Error loading employees list.";
        }
    }
    
    _onEmployeeSearch(event) {
        const query = event.target.value.toLowerCase();
        this.state.employeeSearchQuery = query;
        
        if (query.length === 0) {
            this.state.filteredEmployees = this.state.employees;
            this.state.showEmployeeDropdown = false;
        } else {
            this.state.filteredEmployees = this.state.employees.filter(employee => 
                employee.name.toLowerCase().includes(query) ||
                (employee.department && employee.department.toLowerCase().includes(query))
            );
            this.state.showEmployeeDropdown = true;
        }
    }
    
    _onEmployeeSearchFocus() {
        if (this.state.employeeSearchQuery) {
            this.state.showEmployeeDropdown = true;
        }
    }
    
    _onEmployeeSearchBlur() {
        // Delay hiding dropdown to allow for click events
        setTimeout(() => {
            this.state.showEmployeeDropdown = false;
        }, 200);
    }
    
    _onEmployeeSelect(event) {
        event.preventDefault();
        const employeeId = event.currentTarget.getAttribute('data-employee-id');
        const employeeName = event.currentTarget.getAttribute('data-employee-name');
        
        this.state.selectedEmployeeId = parseInt(employeeId);
        this.state.selectedEmployeeName = employeeName;
        this.state.employeeSearchQuery = employeeName;
        this.state.showEmployeeDropdown = false;
        
        // Update form fields
        this.inputHostingEmployeeSearchRef.el.value = employeeName;
        this.inputHostingEmployeeRef.el.value = employeeId;
    }
    
    _addVisitor() {
        const newVisitor = {
            id: this.state.nextVisitorId++,
            name: '',
            email: '',
            phone: '',
            idNumber: ''
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
        const hostingEmployeeId = this.inputHostingEmployeeRef.el.value;
        const visitDate = this.inputVisitDateRef.el.value;
        const visitTime = this.inputVisitTimeRef.el.value;
        
        if (!companyName || !hostingEmployeeId || !visitDate || !visitTime) {
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
                hosting_employee_id: parseInt(hostingEmployeeId),
                visit_date: visitDate,
                visit_time: visitTime,
                visitors: this.state.visitors.map(visitor => ({
                    name: visitor.name,
                    email: visitor.email,
                    phone: visitor.phone,
                    id_number: visitor.idNumber
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
        this.inputHostingEmployeeSearchRef.el.value = '';
        this.inputVisitDateRef.el.value = '';
        this.inputVisitTimeRef.el.value = '';
        this.state.visitors = [];
        this.state.nextVisitorId = 1;
        this.state.errorMessage = null;
        this.state.selectedEmployeeId = null;
        this.state.selectedEmployeeName = '';
        this.state.employeeSearchQuery = '';
        this.state.showEmployeeDropdown = false;
        this.state.filteredEmployees = this.state.employees;
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
