# -*- coding: utf-8 -*-
from ast import literal_eval
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """
    Extend the 'res.config.settings' model to manage configuration settings for
     enabling/disabling the chatter feature.
    """
    _inherit = 'res.config.settings'

    model_ids = fields.Many2many('ir.model', string="Models",
                                 help="Choose the models to hide their "
                                      "chatter")

    def set_values(self):
        """
        Override the 'set_values' method to save the selected models as
        configuration parameters.
        """
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'hide_chatter.model_ids', self.model_ids.ids)
        return res

    @api.model
    def get_values(self):
        """
        Override the 'get_values' method to retrieve the selected models from
        configuration parameters.
        """
        res = super(ResConfigSettings, self).get_values()
        selected_models = self.env['ir.config_parameter'].sudo().get_param(
            'hide_chatter.model_ids')
        res.update(model_ids=[(6, 0, literal_eval(
            selected_models))] if selected_models else False, )
        return res
