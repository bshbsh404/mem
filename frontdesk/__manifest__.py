# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Frontdesk',
    'category': 'Human Resources/Frontdesk',
    'description': 'A comprehensive front desk management system that enables guests to effortlessly check in and out while ensuring seamless notifications for hosts.',
    'summary': 'Visitor management system',
    'installable': True,
    'application': True,
    'license': 'OEEL-1',
    'version': '1.0',
    'depends': ['hr', 'operating_unit', 'portal'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/frontdesk_cron.xml',
        'data/frontdesk_auto_delete_cron.xml',
        'views/frontdesk_report_views.xml',
        'views/frontdesk_drink_views.xml',
        'views/frontdesk_visitor_views.xml',
        'views/frontdesk_frontdesk_views.xml',
        'views/frontdesk_menus.xml',
        'views/frontdesk_templates.xml',
        'views/frontdesk_qr_expiration.xml',
        'views/res_partner_views.xml',
        'views/frontdesk_request_views.xml',
        'reports/visit_report.xml',
        'data/mail_template_data.xml',
        'data/sms_template_data.xml',
        'data/frontdesk_data.xml',
        'views/visit_purpose_views.xml',
        'views/visit_reassignment_request.xml',
        'views/employee_availability.xml',
        'views/frontdesk_holiday.xml',
        'views/buildings_hierarchy.xml',
        'views/hr_employee_building_views.xml',
        'views/sms_config.xml',
        'views/recaptcha_config.xml',
        'views/portal_employee.xml',
        'views/hr_department.xml',
        'views/templates.xml',
        'views/visit_report_wizard_views.xml',
    ],
    'demo': [
        'demo/frontdesk_demo.xml',
    ],
    'assets': {
        "web.assets_frontend": [
            "frontdesk/static/src/portal_employee_location.js",
            "frontdesk/static/src/portal_employee_location.css",
        ],
        'frontdesk.assets_frontdesk': [
            # QR Scanner
            "frontdesk/static/src/qrScanner.js",

            # 1 Define frontdesk variables (takes priority over frontend ones)
            "frontdesk/static/src/primary_variables.scss",
            "frontdesk/static/src/bootstrap_overridden.scss",

            #2 Load frontend variables
            ("include", "web._assets_helpers"),
            ("include", "web._assets_frontend_helpers"),
            ("include", "web._assets_primary_variables"),
            "web/static/src/scss/pre_variables.scss",

            #3 Load Bootstrap and frontend bundles
            "web/static/lib/bootstrap/scss/_functions.scss",
            "web/static/lib/bootstrap/scss/_variables.scss",
            ("include", "web._assets_bootstrap_frontend"),

            #4 Frontdesk's specific assets
            'web/static/lib/zxing-library/zxing-library.js',
            'frontdesk/static/src/**/*',
        ],
        'web.assets_tests': [
            'frontdesk/static/tests/tours/**/*',
        ],
        'web.assets_backend': [
            'frontdesk/static/backend/css/*',
        ],
    },
}
