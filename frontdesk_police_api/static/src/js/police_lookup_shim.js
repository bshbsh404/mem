/** @odoo-module **/

import { Component } from "@odoo/owl";

/* أدوات مساعدة */
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

    // (اختياري) اختر Civil ID تلقائيًا
    var radioVisitorId = document.getElementById("selectVisitorID");
    if (radioVisitorId && !radioVisitorId.checked) {
        radioVisitorId.checked = true;
        fireChange(radioVisitorId);
    }
}

/* Shim: يضيف الهاندلر الحقيقي مباشرةً على كل الـ Components */
if (!Component.prototype._onPoliceIdLookup) {
    Component.prototype._onPoliceIdLookup = async function (ev) {
        if (ev && ev.preventDefault) ev.preventDefault();

        // حضّر الحالة
        if (!this.state) this.state = {};
        this.state.policeApiError = null;
        this.state.policeDataFound = false;
        this.state.isPoliceApiLoading = true;
        if (this.render) this.render();

        // احصل على القيم من DOM أو refs
        var civilId =
            (document.getElementById("police_civil_id") && document.getElementById("police_civil_id").value) ||
            (this.inputPoliceCivilIDRef && this.inputPoliceCivilIDRef.el && this.inputPoliceCivilIDRef.el.value) ||
            (this.inputVisitorIDRef && this.inputVisitorIDRef.el && this.inputVisitorIDRef.el.value) ||
            "";
        civilId = civilId ? civilId.trim() : "";

        var cardExpEl = document.getElementById("card_expiry");
        var cardExpiry = cardExpEl && cardExpEl.value ? cardExpEl.value : "";

        if (!civilId || civilId.length < 4) {
            this.state.isPoliceApiLoading = false;
            this.state.policeApiError = "يرجى إدخال رقم البطاقة المدنية صحيح";
            if (this.render) this.render();
            return;
        }
        if (!cardExpiry) {
            this.state.isPoliceApiLoading = false;
            this.state.policeApiError = "يرجى إدخال تاريخ انتهاء البطاقة";
            if (this.render) this.render();
            return;
        }

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

                // حدّث الـ parent إن وُجد
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

                // حالة واجهة لرسالة النجاح
                for (var k in payload) { this.state[k] = payload[k]; }
                this.state.policeDataFound = true;
                if (this.render) this.render();

                // ملء يدوي الآن وبعد لحظات (لمعالجة أي re-render)
                setTimeout(() => applyPayloadToInputs(this, payload), 0);
                setTimeout(() => applyPayloadToInputs(this, payload), 200);
                setTimeout(() => applyPayloadToInputs(this, payload), 800);

                try {
                    console.log("✅ Data found successfully! Form filled automatically.");
                    console.log("📌 Visitor Data:", payload);
                } catch (e) {}
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
    };
}
