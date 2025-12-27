/** @odoo-module **/

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { Component } from "@odoo/owl";

/* --------- 0) Stub: يمنع Invalid handler لو ضغط الزر قبل تحميل الباتش --------- */
if (!Component.prototype._onPoliceIdLookup) {
    Component.prototype._onPoliceIdLookup = function (ev) {
        if (ev && ev.preventDefault) ev.preventDefault();
        if (!this.state) this.state = {};
        this.state.policeApiError = "Police lookup not ready yet. Please try again.";
        if (this.render) this.render();
        console.warn("[PoliceLookup] Stub handler: patch not installed yet.");
    };
}

/* --------- أدوات مساعدة للملء اليدوي --------- */
function fireChange(el) {
    try {
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
    } catch (e) {}
}
function setField(ref, id, val) {
    if (val === undefined || val === null || val === "") return;
    if (ref && ref.el) {
        ref.el.value = val;
        fireChange(ref.el);
        return;
    }
    if (id) {
        var el = document.getElementById(id);
        if (el) {
            el.value = val;
            fireChange(el);
        }
    }
}
function applyPayloadToInputs(ctx, p) {
    setField(ctx.inputNameRef,       "name",         p.visitorName);
    setField(ctx.inputSecondNameRef, "second_name",  p.visitorSecondName);
    setField(ctx.inputThirdNameRef,  "third_name",   p.visitorThirdName);
    setField(ctx.inputFourthNameRef, "fourth_name",  p.visitorFourthName);
    setField(ctx.inputPhoneRef,      "phone",        p.visitorPhone);
    setField(ctx.inputEmailRef,      "email",        p.visitorEmail);
    setField(ctx.inputVisitorIDRef,  "visitor_id",   p.visitorID);

    // اختر Civil ID تلقائيًا (اختياري)
    var radioVisitorId = document.getElementById("selectVisitorID");
    if (radioVisitorId && !radioVisitorId.checked) {
        radioVisitorId.checked = true;
        fireChange(radioVisitorId);
    }
}

/* --------- 1) باتش على VisitorForm --------- */
function installOnce(VF) {
    if (!VF || VF.prototype._policePatchInstalled) return;
    VF.prototype._policePatchInstalled = true;
    console.log("[PoliceLookup] Patch installed on VisitorForm");

    patch(VF.prototype, "visitor_form_police_patch", {
        setup: function () {
            if (this._super) this._super.apply(this, arguments);
            if (!this.state) this.state = {};
            if (typeof this.state.isPoliceApiLoading === "undefined") this.state.isPoliceApiLoading = false;
            if (typeof this.state.policeApiError === "undefined") this.state.policeApiError = null;
            if (typeof this.state.policeDataFound === "undefined") this.state.policeDataFound = false;
        },

        _onPoliceIdLookup: async function (ev) {
            if (ev && ev.preventDefault) ev.preventDefault();

            var civilIdEl   = document.getElementById("police_civil_id");
            var cardExpEl   = document.getElementById("card_expiry");
            var civilId     = civilIdEl && civilIdEl.value ? civilIdEl.value.trim() : "";
            var cardExpiry  = cardExpEl && cardExpEl.value ? cardExpEl.value : "";

            if (!civilId || civilId.length < 4) {
                this.state.policeApiError = "يرجى إدخال رقم البطاقة المدنية صحيح";
                this.state.policeDataFound = false;
                if (this.render) this.render();
                return;
            }
            if (!cardExpiry) {
                this.state.policeApiError = "يرجى إدخال تاريخ انتهاء البطاقة";
                this.state.policeDataFound = false;
                if (this.render) this.render();
                return;
            }

            this.state.isPoliceApiLoading = true;
            this.state.policeApiError = null;
            if (this.render) this.render();

            try {
                var rpc = (this.env && this.env.services && this.env.services.rpc) || this.rpc;
                if (!rpc) throw new Error("RPC service not available");

                var result = await rpc("/frontdesk/police_api/get_visitor_data", {
                    civil_id: civilId,
                    card_expiry: cardExpiry,
                    context: { lang: (this.props && this.props.currentLang) || "ar" },
                });

                if (result && result.success && result.data) {
                    var d = result.data || {};
                    var payload = {
                        visitorName:        d.name || "",
                        visitorSecondName:  d.second_name || "",
                        visitorThirdName:   d.third_name || "",
                        visitorFourthName:  d.fourth_name || "",
                        visitorPhone:       d.phone || "",
                        visitorEmail:       d.email || "",
                        visitorID:          civilId,
                    };

                    // حدّث الأب لو عنده setVisitorData
                    if (this.props && typeof this.props.setVisitorData === "function") {
                        this.props.setVisitorData(
                            payload.visitorName || false,
                            payload.visitorSecondName || false,
                            payload.visitorThirdName || false,
                            payload.visitorFourthName || false,
                            payload.visitorPhone || false,
                            false, // landline
                            payload.visitorEmail || false,
                            false, // company
                            payload.visitorID || false,
                            false, // passport
                            false  // emp_id
                        );
                    } else if (this.props && this.props.visitorData && typeof this.props.visitorData === "object") {
                        Object.assign(this.props.visitorData, payload);
                    }

                    // حالة لرسالة النجاح وإعادة الملء لاحقًا
                    Object.assign(this.state, { policeDataFound: true }, payload);
                    if (this.render) this.render();

                    // ملء يدوي الآن وبعد أي re-render عابر
                    setTimeout(() => applyPayloadToInputs(this, payload), 0);
                    setTimeout(() => applyPayloadToInputs(this, payload), 200);
                    setTimeout(() => applyPayloadToInputs(this, payload), 800);

                    console.log("✅ Data found successfully! Form filled automatically.");
                    console.log("📌 Visitor Data:", payload);
                } else {
                    this.state.policeApiError = (result && result.error) || "لم يتم العثور على البيانات";
                    this.state.policeDataFound = false;
                }
            } catch (e) {
                console.error("Police API error:", e);
                this.state.policeApiError = "خطأ في الاتصال بقاعدة بيانات الشرطة";
                this.state.policeDataFound = false;
            } finally {
                this.state.isPoliceApiLoading = false;
                if (this.render) this.render();
            }
        },

        mounted: async function () {
            if (this._super) this._super.apply(this, arguments);
            if (this.state && this.state.policeDataFound) {
                setTimeout(() => applyPayloadToInputs(this, this.state), 0);
            }
        },
        patched: async function () {
            if (this._super) this._super.apply(this, arguments);
            if (this.state && this.state.policeDataFound) {
                setTimeout(() => applyPayloadToInputs(this, this.state), 0);
            }
        },
    });
}

/* --------- 2) مثبّت بمحاولات حتى يظهر VisitorForm في الريجيستري --------- */
(function tryInstall(retries) {
    try {
        var cat = registry.category("frontdesk_screens");
        var VF = cat && cat.get && cat.get("VisitorForm");
        if (VF) {
            installOnce(VF);
            return;
        }
    } catch (e) {
        console.warn("[PoliceLookup] registry not ready yet:", e && e.message);
    }
    if (retries > 0) {
        setTimeout(function () { tryInstall(retries - 1); }, 250);
    } else {
        console.warn("[PoliceLookup] VisitorForm not found; patch not installed.");
    }
})(30); // يحاول ~7.5 ثانية
