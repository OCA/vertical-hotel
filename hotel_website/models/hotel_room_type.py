# Copyright (C) 2019-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import ClassVar

from odoo import api, fields, models


class HotelRoomType(models.Model):
    _name = "hotel.room.type"
    _inherit: ClassVar[list] = ["hotel.room.type", "image.mixin"]

    website_description = fields.Html(
        translate=True,
        help="Shown to guests on the room type's page.",
    )
    website_sequence = fields.Integer(
        default=10, help="Order of the room types on the website."
    )
    room_review_ids = fields.One2many(
        "room.review", "room_type_id", string="Website Reviews"
    )
    website_review_count = fields.Integer(compute="_compute_website_review_stats")
    website_review_avg = fields.Float(
        "Website Average Rating",
        compute="_compute_website_review_stats",
        digits=(2, 1),
    )

    @api.depends("room_review_ids.rating", "room_review_ids.is_published")
    def _compute_website_review_stats(self):
        groups = (
            self.env["room.review"]
            .sudo()
            ._read_group(
                [("room_type_id", "in", self._origin.ids), ("is_published", "=", True)],
                ["room_type_id"],
                ["__count", "rating:avg"],
            )
        )
        stats = {room_type.id: (count, avg) for room_type, count, avg in groups}
        for room_type in self:
            count, avg = stats.get(room_type._origin.id, (0, 0.0))
            room_type.website_review_count = count
            room_type.website_review_avg = avg or 0.0
