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
    # Reviews come from the public website: they wait for the hotel to
    # publish them.
    is_published = fields.Boolean(
        "Published",
        default=False,
        help="Tick to show this review on the website.",
    )

    @api.model
    def _hotel_review_status(self, partner, room_type):
        """Whether ``partner`` may review ``room_type`` on the website.

        :return: ``"allowed"``, ``"reviewed"`` (one review per guest and
            room type) or ``"no_stay"`` (only guests who stayed, or have a
            confirmed stay, in a room of that type may review it)
        """
        if self.sudo().search_count(
            [("partner_id", "=", partner.id), ("room_type_id", "=", room_type.id)],
            limit=1,
        ):
            return "reviewed"
        guest = partner.commercial_partner_id
        has_reservation = (
            self.env["hotel.reservation"]
            .sudo()
            .search_count(
                [
                    ("partner_id", "child_of", guest.id),
                    ("state", "in", ("confirm", "done")),
                    "|",
                    ("reservation_line.categ_id", "=", room_type.id),
                    ("reservation_line.reserve.room_categ_id", "=", room_type.id),
                ],
                limit=1,
            )
        )
        has_stay = has_reservation or (
            self.env["folio.room.line"]
            .sudo()
            .search_count(
                [
                    ("folio_id.partner_id", "child_of", guest.id),
                    ("folio_id.state", "=", "sale"),
                    ("room_id.room_categ_id", "=", room_type.id),
                ],
                limit=1,
            )
        )
        return "allowed" if has_stay else "no_stay"

    @api.constrains("rating")
    def _check_rating(self):
        for review in self:
            if not 1 <= review.rating <= 5:
                raise ValidationError(
                    self.env._("A review rating must be between 1 and 5.")
                )

    @api.constrains("partner_id", "room_type_id")
    def _check_one_review_per_guest(self):
        for review in self.filtered("partner_id"):
            others = self.search_count(
                [
                    ("id", "!=", review.id),
                    ("partner_id", "=", review.partner_id.id),
                    ("room_type_id", "=", review.room_type_id.id),
                ]
            )
            if others:
                raise ValidationError(
                    self.env._(
                        "%(guest)s has already reviewed %(room_type)s.",
                        guest=review.partner_id.display_name,
                        room_type=review.room_type_id.display_name,
                    )
                )
