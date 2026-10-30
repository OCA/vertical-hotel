# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RoomReview(models.Model):
    _name = "room.review"
    _description = "Hotel Room Review"
    _order = "create_date desc, id desc"

    room_type_id = fields.Many2one(
        "hotel.room.type", required=True, ondelete="cascade", index=True
    )
    partner_id = fields.Many2one(
        "res.partner", "Reviewer", ondelete="set null", index=True
    )
    name = fields.Char("Reviewer Name", required=True)
    rating = fields.Integer(required=True, default=5)
    comment = fields.Text()
    is_published = fields.Boolean(
        "Published",
        default=True,
        help="Untick to hide this review from the website.",
    )

    @api.constrains("rating")
    def _check_rating(self):
        for review in self:
            if not 1 <= review.rating <= 5:
                raise ValidationError(
                    self.env._("A review rating must be between 1 and 5.")
                )
