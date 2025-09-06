/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onDestroy, onWillUnmount, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CancelVisit extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.qrCode = '';
        this.html5Qrcode = false;

        onMounted(this.showQrScanner);
    }

    showQrScanner() {
        var self = this;
        const html5Qrcode = new Html5Qrcode('reader');
        const config = {fps:10, qrbox:{width:500, height:500}}
        const qrCodeSuccessCallback = (decodedText, decodedResult)=>{
            if(decodedText){
                self.qrCode = decodedText;
                html5Qrcode.stop().then((ignore) => {
                    console.log("Scanning stopped.");
                });
                self.uploadQrData()
            }
        }
        self.html5Qrcode = html5Qrcode;
        html5Qrcode.start({facingMode:"environment"}, config, qrCodeSuccessCallback);
    }

    async uploadQrData() {
        $('#cancelModal').modal('show');

    }

    async _onSubmitCancellation() {
        var reason = document.getElementById("cancel_reason").value;
        if(reason == ""){
            alert("Please enter a reason for cancellation");
            return;
        }
        const result = await this.rpc(`${this.props.frontdeskUrl}/frontdesk_cancel_visit`, {
            qrCode: this.qrCode,
            reason: reason
        });

        alert(result.message);
        this.props.showScreen("WelcomePage");

    }

    /**
     * @private
     */
    _onSubmit() {
        this.showQrScanner();
    }
}

CancelVisit.template = "frontdesk.CancelVisit";
CancelVisit.props = {
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

registry.category("frontdesk_screens").add("CancelVisit", CancelVisit);
