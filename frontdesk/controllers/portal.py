# controllers/portal_ext.py
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request

class CustomerPortalExt(CustomerPortal):
    CUSTOM_EMP_FIELDS = {'building_id', 'level_id', 'section_id', 'location_description'}

    # 1) Ignore our custom fields in portal validation to avoid "Unknown field"
    def details_form_validate(self, data, partner_creation=False):
        filtered = {k: v for k, v in data.items() if k not in self.CUSTOM_EMP_FIELDS}
        return super().details_form_validate(filtered, partner_creation)

    # 2) Write to hr.employee and make sure partner vals don't contain our keys
    def on_account_update(self, values, partner):
        # ensure partner.write won't see these keys even if they slip in
        for k in list(self.CUSTOM_EMP_FIELDS):
            values.pop(k, None)

        params = request.params  # POST payload
        emp = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        if not emp:
            return

        def to_int(v):
            try:
                return int(v) if v not in (None, '', False) else False
            except Exception:
                return False

        emp_vals = {
            'building_id': to_int(params.get('building_id')),
            'level_id': to_int(params.get('level_id')),
            'section_id': to_int(params.get('section_id')),
            'location_description': params.get('location_description') or False,
        }
        emp.write(emp_vals)
