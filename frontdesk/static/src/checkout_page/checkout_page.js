/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, useState, onDestroy, onWillUnmount, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CheckOut extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.qrCode = '';
        this.html5Qrcode = false;
        this.state = useState({
            nfcCardNumber: '',
            selectedEvaluation: null,
            visitorName: '',
            comment: '',   
        });

        onMounted(this.showQrScanner);
    }

    showQrScanner() {
        var self = this;
        console.log("checkout showQrScanner");
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
        const result = await this.rpc(`${this.props.frontdeskUrl}/frontdesk_check_out`, {
            qrCode: this.qrCode
        });
        console.log("uploadQrData");

        // check if the result includes the NFC card number
        if (result.visitor_name){
            this.state.visitorName = result.visitor_name;
        }
        if (result.nfc_card_number){
            this.state.nfcCardNumber = result.nfc_card_number;
        }
        console.log(result);

        $('#evaluationModal').modal('show');
        // }else{
        //     alert(result.message);
        //     this.props.showScreen("WelcomePage");
        // }

    }

    _onSelectEmoji(rating) {
        this.state.selectedEvaluation = rating;
    }

    async _onSubmitEvaluation(evaluation) {
        if (!this.state.selectedEvaluation) {
            alert('Please select an evaluation');
            return;
        }
        const result = await this.rpc(`${this.props.frontdeskUrl}/submit_evaluation`, {
            qrCode: this.qrCode,
            evaluation: this.state.selectedEvaluation,
            comment: this.state.comment,
        });

        // Close the modal and redirect to the WelcomePage
        $('#evaluationModal').modal('hide');
        this.props.showScreen("WelcomePage");
    }

    /**
     * @private
     */
    _onSubmit() {
        this.showQrScanner();
    }
}

CheckOut.template = "frontdesk.CheckOut";
CheckOut.props = {
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

registry.category("frontdesk_screens").add("CheckOut", CheckOut);
