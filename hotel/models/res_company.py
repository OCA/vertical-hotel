# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    additional_hours = fields.Integer(
        help="Provide the min hours value for \
                                      check in, checkout days, whatever the \
                                      hours will be provided here based on \
                                      that extra days will be calculated.",
    )
