/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onDestroy, onWillUnmount, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ExtendVisit extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.qrCode = '';
        this.visitorId = null;
        this.html5Qrcode = false;
        this.state = useState({
            showPopup: false,  // Control visibility of the extension popup
            extensionTime: 0,  // Store the extension time
            errorMessage: null,  // Handle error messages
        });

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
        const result = await this.rpc(`${this.props.frontdeskUrl}/frontdesk_extend_visit`, {
            qrCode: this.qrCode
        });
        if (result.success) {
            this.visitorId = result.id;
            this.state.showPopup = true;  // Show the popup to request the extension
        } else {
            this.state.errorMessage = result.message;
        }
    }

    async submitExtension() {
        if (this.state.extensionTime <= 0) {
            this.state.errorMessage = "Please enter a valid extension time.";
            return;
        }

        const result = await this.rpc(`${this.props.frontdeskUrl}/update_extension`, {
            visitor_id: this.visitorId,
            extension: this.state.extensionTime
        });

        if (result.success) {
            this.state.showPopup = false;
            this.state.errorMessage = null;
            // alert(result.message);  // Display success message (you can replace this with better UI feedback)
            this.props.showScreen("WelcomePage");
        } else {
            this.state.errorMessage = result.message;
        }
    }

    /**
     * @private
     */
    _onSubmit() {
        this.showQrScanner();
    }
}

ExtendVisit.template = "frontdesk.ExtendVisit";
ExtendVisit.props = {
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

registry.category("frontdesk_screens").add("ExtendVisit", ExtendVisit);
