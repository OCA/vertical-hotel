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
    hotel_layout = fields.Boolean(related="website_id.hotel_layout", readonly=False)
    hotel_request_expiry_days = fields.Integer(
        "Request Expiry (Days)",
        config_parameter="hotel_website.request_expiry_days",
        default=3,
        help="Website requests the front desk has not confirmed after this "
        "many days are cancelled and the guest is told. 0: only when the "
        "arrival date has passed.",
    )
