from odoo import http
from odoo.http import request

class TestErrorController(http.Controller):

    @http.route('/test/error', type='http', auth='public', website=True)
    def test_error(self):
        # Intentional error: division by zero
        return str(1 / 0)