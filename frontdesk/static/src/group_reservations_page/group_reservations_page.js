/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onDestroy, onWillUnmount, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class GroupReservations extends Component {
    setup() {
        this.rpc = useService("rpc");
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
