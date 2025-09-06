/** @odoo-module **/

import { registry } from "@web/core/registry";
import { VisitorForm } from "@frontdesk/visitor_form/visitor_form";
import { CheckIn } from "@frontdesk/checkin_page/checkin_page";
import { CheckOut } from "@frontdesk/checkout_page/checkout_page";
import { CancelVisit } from "@frontdesk/cancel_visit_page/cancel_visit_page";
import { GroupReservations } from "@frontdesk/group_reservations_page/group_reservations_page";
import { ExtendVisit } from "@frontdesk/extend_visit_page/extend_visit_page";
import { WelcomePage } from "@frontdesk/welcome_page/welcome_page";
import { RegisterPage } from "@frontdesk/register_page/register_page";
import { DrinkPage } from "@frontdesk/drink_page/drink_page";
import { Navbar } from "@frontdesk/navbar/navbar";
import { HostPage } from "@frontdesk/host_page/host_page";
import { EndPage } from "@frontdesk/end_page/end_page";
import { QuickCheckIn } from "@frontdesk/quick_check_in/quick_check_in";
import { useService } from "@web/core/utils/hooks";

import { Component, useState, onWillStart, markup } from "@odoo/owl";

export class Frontdesk extends Component {
    setup() {
        this.state = useState({
            currentComponent: !this.props.isMobile ? WelcomePage : VisitorForm,
            plannedVisitors: [],
        });
        const urlToken = window.location.href.split("/").findLast((s) => s);
        this.token = urlToken.includes("?") ? urlToken.split("?")[0] : urlToken;
        this.frontdeskUrl = `/frontdesk/${this.props.id}/${this.token}`;
        this.rpc = useService("rpc");
        onWillStart(this.onWillStart);
        if (this.props.isMobile) {
            // Retrieve the saved component from sessionStorage
            const savedComponent = sessionStorage.getItem("currentComponent");
            if (savedComponent) {
                const component = registry.category("frontdesk_screens").get(savedComponent);
                this.state.currentComponent = component;
            }
            window.addEventListener("beforeunload", () => {
                // Before the page refresh, save the current component to sessionStorage
                sessionStorage.setItem("currentComponent", this.state.currentComponent.name);
            });
        }
    }

    async onWillStart() {
        const urlParams = new URLSearchParams(window.location.search);
        const lang = urlParams.get('lang');
        this.frontdeskData = await this.rpc(`${this.frontdeskUrl}/${lang}/get_frontdesk_data`);
        this.station = this.frontdeskData.station[0];
    }

    /* This method updates the plannedVisitors */
    updatePlannedVisitors() {
        this._getPlannedVisitors();
        this.intervalId = setInterval(() => this._getPlannedVisitors(), 600000); // 10 minutes
    }

    /**
     * Get the plannedVisitors from the backend through rpc call
     *
     * @private
     */
    async _getPlannedVisitors() {
        this.state.plannedVisitors = await this.rpc(`${this.frontdeskUrl}/get_planned_visitors`);
    }

    /* This method creates the visitor in the backend through rpc call */
    async createVisitor() {
        console.log('Visitor Data:', this.visitorData);
        console.log('host Data:', this.hostData);
        const result = await this.rpc(`${this.frontdeskUrl}/prepare_visitor_data`, {
            name: this.visitorData.visitorName,
            second_name: this.visitorData.visitorSecondName,
            third_name: this.visitorData.visitorThirdName,
            fourth_name: this.visitorData.visitorFourthName,
            phone: this.visitorData.visitorPhone,
            landline: this.visitorData.visitorLandline,
            email: this.visitorData.visitorEmail,
            company: this.visitorData.visitorCompany,
            host_ids: this.hostData ? [this.hostData.hostId] : [],
            host_name: this.hostData ? [this.hostData.hostEmployeeName] : [],
            host_phone: this.hostData ? [this.hostData.hostPhone] : [],
            host_email: this.hostData ? [this.hostData.hostEmail] : [],
            is_recurring: this.hostData ? this.hostData.isRecurring : false,
            planned_date: this.hostData ? this.hostData.plannedDate : false,
            planned_date_end: this.hostData ? this.hostData.plannedDateEnd : false,
            planned_time: this.hostData ? this.hostData.plannedTime : false,
            planned_duration: this.hostData ? this.hostData.plannedDuration : false,
            visit_purpose: this.hostData ? this.hostData.purpose : false,
            other_reason: this.hostData ? this.hostData.other_reason : false,
            host_landline: this.hostData ? this.hostData.landline : false,
            visitor_card : this.visitorData.visitorId,
            passport: this.visitorData.passport,
            emp_id: this.visitorData.emp_id,
            visit_type: this.hostData && this.hostData.visit_type ? this.hostData.visit_type : false,
            wilayat: this.hostData && this.hostData.wilayat ? this.hostData.wilayat : false,
            recaptcha_response: this.hostData && this.hostData.recaptcha_response ? this.hostData.recaptcha_response : false,
            preferred_language: this.props.currentLang  != null ? this.props.currentLang : "en_US",
        });
        // this.visitorId = result.visitor_id;
    }

    onClose() {
        // Check if the device is mobile or not and show the screen accordingly
        !this.props.isMobile ? this.showScreen("WelcomePage") : this.showScreen("VisitorForm");
    }

    /**
     * @param {Event} ev
     */
    onChangeLang(ev) {
        window.location.href = window.location.pathname + `?lang=${encodeURIComponent(ev.currentTarget.value)}`;
    }

    /**
     * This method change the current screen
     *
     * @param {string} name
     */
    showScreen(name) {
        const component = registry.category("frontdesk_screens").get(name);
        this.state.currentComponent = component;
    }

    /* This method clears the interval for updatePlannedVisitors */
    clearUpdatePlannedVisitors() {
        clearInterval(this.intervalId);
    }

    /* Reset the data */
    resetData() {
        this.hostData = null;
        this.visitorData = null;
        this.plannedVisitorData = null;
        this.isDrinkSelected = false;
    }

    /**
     * @param {string} name
     * @param {string|false} phone
     * @param {string|false} email
     * @param {string|false} company
     */
    setVisitorData(
        name, secondName,
        thirdName, fourthName,
        phone, landline,
        email, company, visitorIdNumber, passport, emp_id) {
            console.log('setVisitorData Visitor Data:', name, secondName, thirdName, fourthName, phone, landline, email, company, visitorIdNumber, passport, emp_id);
        this.visitorData = {
            visitorName: name,
            visitorSecondName: secondName,
            visitorThirdName: thirdName,
            visitorFourthName: fourthName,
            visitorPhone: phone,
            visitorLandline: landline,
            visitorEmail: email,
            visitorCompany: company,
            visitorId: visitorIdNumber,
            passport: passport,
            emp_id: emp_id,
        };
    }

    /**
     * @param {Object} host
     */
    setHostData(host, name, phone, email, isRecurring, plannedDate, plannedDateEnd, plannedTime, plannedDuration, purpose, other_reason, landline, visit_type, wilayat, recaptcha_response, language) {
        this.hostData = {
            hostId: host.id,
            hostName: host.display_name,
            hostEmployeeName: name,
            hostPhone: phone,
            hostEmail: email,
            isRecurring: isRecurring,
            plannedDate: plannedDate,
            plannedDateEnd: plannedDateEnd,
            plannedTime: plannedTime,
            plannedDuration: plannedDuration,
            purpose: purpose,
            other_reason: other_reason,
            landline: landline,
            visit_type: visit_type,
            wilayat: wilayat,
            recaptcha_response: recaptcha_response,
            preferred_language: language,
        };
        console.log('setHostData Host Data:', this.hostData);
    }

    /**
     * @param {number} plannedVisitorId
     * @param {string|false} plannedVisitorMessage
     * @param {Array} plannedVisitorHosts
     */
    setPlannedVisitorData(plannedVisitorId, plannedVisitorMessage, plannedVisitorHosts) {
        this.plannedVisitorData = {
            plannedVisitorId: plannedVisitorId,
            plannedVisitorMessage: plannedVisitorMessage,
            plannedVisitorHosts: plannedVisitorHosts,
        };
    }

    /**
     * @param {boolean} boolean
     */
    setDrink(boolean) {
        this.isDrinkSelected = boolean;
    }

    // -------------------------------------------------------------------------
    // Getters
    // -------------------------------------------------------------------------

    get frontdeskProps() {
        let props = {};
        if (this.state.currentComponent === WelcomePage) {
            props = {
                showScreen: this.showScreen.bind(this),
                resetData: this.resetData.bind(this),
                onChangeLang: this.onChangeLang.bind(this),
                token: this.token,
                companyName: this.frontdeskData.company.name,
                companyID: this.frontdeskData.company.id,
                stationInfo: this.station,
                langs: this.frontdeskData.langs.length > 1 ? this.frontdeskData.langs : false,
                currentLang: this.props.currentLang,
            };
        } else if (this.state.currentComponent === VisitorForm || this.state.currentComponent === CheckIn
            || this.state.currentComponent === ExtendVisit || this.state.currentComponent === CancelVisit
            || this.state.currentComponent === CheckOut || this.state.currentComponent === GroupReservations
        ) {
            props = {
                onChangeLang: this.onChangeLang.bind(this),
                showScreen: this.showScreen.bind(this),
                clearUpdatePlannedVisitors: this.clearUpdatePlannedVisitors.bind(this),
                setVisitorData: this.setVisitorData.bind(this),
                updatePlannedVisitors: this.updatePlannedVisitors.bind(this),
                visitorData: this.visitorData || false,
                isMobile: this.props.isMobile,
                currentComponent: this.state.currentComponent.name,
                isPlannedVisitors: this.state.plannedVisitors.length ? true : false,
                stationInfo: this.station,
                langs: this.frontdeskData.langs.length > 1 ? this.frontdeskData.langs : false,
                currentLang: this.props.currentLang,
                theme: this.station.theme,
                frontdeskUrl: this.frontdeskUrl

            };
        } else if (this.state.currentComponent === HostPage) {
            props = {
                stationId: this.station.id,
                stationInfo: this.station,
                token: this.token,
                showScreen: this.showScreen.bind(this),
                setHostData: this.setHostData.bind(this),
                theme: this.station.theme,
            };
        } else if (this.state.currentComponent === RegisterPage) {
            props = {
                showScreen: this.showScreen.bind(this),
                onClose: this.onClose.bind(this),
                createVisitor: this.createVisitor.bind(this),
                theme: this.station.theme,
                isMobile: this.props.isMobile,
                isDrinkVisible: this.frontdeskData.drinks?.length ? true : false,
                plannedVisitorData: this.plannedVisitorData,
                hostData: this.hostData,
            };
        } else if (this.state.currentComponent === DrinkPage) {
            props = {
                showScreen: this.showScreen.bind(this),
                setDrink: this.setDrink.bind(this),
                theme: this.station.theme,
                drinkInfo: this.frontdeskData.drinks,
                stationId: this.props.id,
                token: this.token,
                visitorId: this.plannedVisitorData
                    ? this.plannedVisitorData.plannedVisitorId
                    : this.visitorId,
            };
        } else if (this.state.currentComponent === EndPage) {
            props = {
                showScreen: this.showScreen.bind(this),
                onClose: this.onClose.bind(this),
                isMobile: this.props.isMobile,
                isDrinkSelected: this.isDrinkSelected,
                theme: this.station.theme,
                plannedVisitorData: this.plannedVisitorData,
                hostData: this.hostData,
            };
        }
        return props;
    }

    get navBarProps() {
        return {
            showScreen: this.showScreen.bind(this),
            currentComponent: this.state.currentComponent.name,
            companyInfo: this.frontdeskData.company,
            isMobile: this.props.isMobile,
            isPlannedVisitors: this.state.plannedVisitors.length ? true : false,
            theme: this.station.theme,
            onChangeLang: this.onChangeLang.bind(this),
            langs: this.frontdeskData.langs.length > 1 ? this.frontdeskData.langs : false,
            currentLang: this.props.currentLang,
        };
    }

    get quickCheckInProps() {
        return {
            setPlannedVisitorData: this.setPlannedVisitorData.bind(this),
            showScreen: this.showScreen.bind(this),
            stationId: this.props.id,
            token: this.token,
            plannedVisitors: this.state.plannedVisitors,
            theme: this.station.theme,
        };
    }

    get markupValue() {
        return markup(this.station.description);
    }
}

Frontdesk.template = "frontdesk.Frontdesk";
Frontdesk.components = {
    WelcomePage,
    Navbar,
    VisitorForm,
    CheckIn,
    QuickCheckIn,
    HostPage,
    RegisterPage,
    DrinkPage,
    EndPage,
};
Frontdesk.props = {
    id: Number,
    isMobile: Boolean,
    currentLang: String,
};

registry.category("public_components").add("frontdesk", Frontdesk);
