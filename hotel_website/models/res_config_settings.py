# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hotel_checkin_hour = fields.Float(
        related="website_id.hotel_checkin_hour", readonly=False
    )
    hotel_checkout_hour = fields.Float(
        related="website_id.hotel_checkout_hour", readonly=False
    )
