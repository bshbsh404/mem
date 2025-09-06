import logging
from odoo import models
from odoo.http import request
from odoo.addons.base.models.ir_http import IrHttp

_logger = logging.getLogger(__name__)

class CustomIrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls, endpoint, *args, **kwargs):
        """ Override Odoo's error handling to hide stack traces. """
        try:
            return super()._dispatch(endpoint, *args, **kwargs)
        except Exception as e:
            # Log full error for debugging
            _logger.error("An error occurred: %s", str(e), exc_info=True)

            # Return a generic error message to hide stack traces
            return request.make_response(
                "An unexpected error occurred. Please contact support.",
                status=500
            )