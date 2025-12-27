/** @odoo-module **/

import { VisitorForm } from "@frontdesk/visitor_form/visitor_form";
import { patch } from "@web/core/utils/patch";

// إضافة زر للتنقل للنموذج الجديد فقط
patch(VisitorForm.prototype, {
    /**
     * دالة للانتقال إلى نموذج البحث في قاعدة بيانات الشرطة
     */
    _goToPoliceForm() {
        this.props.showScreen("PoliceVisitorForm");
    }
});