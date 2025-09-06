/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillUnmount, onMounted } from "@odoo/owl";

const { DateTime } = luxon;

export class WelcomePage extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({ today: this.getCurrentTime(), qrCode: false, isFullScreen: !!document.fullscreenElement });
        this.timeInterval = setInterval(() => (this.state.today = this.getCurrentTime()), 1000);
        this.props.resetData();

        // Make the qr code only when self_check_in field is true from backend.
        if (this.props.stationInfo.self_check_in) {
            this._getQrCodeData();
            this.qrCodeInterval = setInterval(() => this._getQrCodeData(), 3600000); // 1 hour
        }

        document.addEventListener("fullscreenchange", this.handleFullscreenExit);
        document.addEventListener("contextmenu", (event) => event.preventDefault());
        
        // onMounted(() => {
        //     this.toggleFullScreen(); // Enter fullscreen on load
        // });
        
        onWillUnmount(() => {
            clearInterval(this.timeInterval);
            if (this.props.stationInfo.self_check_in) {
                clearInterval(this.qrCodeInterval);
            }

            document.removeEventListener("fullscreenchange", this.handleFullscreenExit);
            document.addEventListener("contextmenu", (event) => event.preventDefault());
        });
    }

    handleFullscreenExit = () => {
        if (!document.fullscreenElement && this.state.isFullScreen) {
            setTimeout(() => {
                // refresh the page
                window.location.reload();
            }, 1000); // 1 second delay
        }
    };

    toggleFullScreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().then(() => {
                this.state.isFullScreen = true;
            }).catch(() => {
                console.log("Fullscreen request blocked by browser settings");
            });
        }
    }

    async exitFullscreen() {
        if(this.props.stationInfo.fullscreen_password === false) { // No password required
            this.state.isFullScreen = document.fullscreenElement !== null;
            try{
                console.log(this.state.isFullScreen);
                try {
                    document.exitFullscreen().then(() => {
                        this.state.isFullScreen = false;
                    });
                } catch (e) {
                    console.log("Fullscreen exit failed", e);
                }
            }catch(e){
                console.log("Fullscreen exit failed");
                console.log(e);
                console.log(this.state.isFullScreen);
            }
        }else{
            const password = await this.promptPassword();
            if (password === this.props.stationInfo.fullscreen_password) { // Change this password
                this.state.isFullScreen = document.fullscreenElement !== null;
                try{
                    console.log(this.state.isFullScreen);
                    try {
                        document.exitFullscreen().then(() => {
                            this.state.isFullScreen = false;
                        });
                    } catch (e) {
                        console.log("Fullscreen exit failed", e);
                    }
                }catch(e){
                    console.log("Fullscreen exit failed");
                    console.log(e);
                    console.log(this.state.isFullScreen);
                }
            } else {
                alert("Incorrect password!");
            }
        }
    }

    async promptPassword() {
        return new Promise((resolve) => {
            const password = prompt("Enter password to exit fullscreen:");
            resolve(password);
        });
    }

    getCurrentTime() {
        return DateTime.now().toLocaleString(DateTime.TIME_SIMPLE);
    }

    /**
     * @private
     */
    async _getQrCodeData() {
        const response = await this.rpc(
            `/kiosk/${this.props.stationInfo.id}/get_tmp_code/${this.props.token}`
        );
        const token = encodeURIComponent(response[0] + response[1]);
        this.state.qrCode = this._makeQrCodeData(
            `${window.location.origin}/kiosk/${this.props.stationInfo.id}/mobile/${token}`
        );
    }

    /**
     * @private
     */
    _makeQrCodeData(url) {
        const codeWriter = new window.ZXing.BrowserQRCodeSvgWriter();
        const qrCodeSVG = new XMLSerializer().serializeToString(codeWriter.write(url, 250, 250));
        return "data:image/svg+xml;base64," + window.btoa(qrCodeSVG);
    }
}

WelcomePage.template = "frontdesk.WelcomePage";
WelcomePage.props = {
    companyName: String,
    companyID: Number,
    currentLang: String,
    langs: [Object, Boolean],
    onChangeLang: Function,
    token: String,
    resetData: Function,
    showScreen: Function,
    stationInfo: Object,
};

registry.category("frontdesk_screens").add("WelcomePage", WelcomePage);
