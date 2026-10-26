# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import timedelta
from itertools import pairwise
from typing import ClassVar

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class FolioRoomLine(models.Model):
    _name = "folio.room.line"
    _description = "Hotel Room Reservation"
    _rec_name = "room_id"

    room_id = fields.Many2one("hotel.room", ondelete="restrict", index=True)
    check_in = fields.Datetime("Check In Date", required=True)
    check_out = fields.Datetime("Check Out Date", required=True)
    folio_id = fields.Many2one("hotel.folio", "Folio Number", ondelete="cascade")
    status = fields.Selection(related="folio_id.state", string="state")


class HotelFolio(models.Model):
    _name = "hotel.folio"
    _description = "hotel folio"
    _inherits: ClassVar[dict] = {"sale.order": "order_id"}
    _rec_name = "order_id"
    _rec_names_search = ("name", "order_id.name")

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.order_id.name or rec.name or ""

    def _default_checkout_date(self):
        return fields.Datetime.now() + timedelta(days=1)

    name = fields.Char("Folio Number", index=True, default="New")
    order_id = fields.Many2one("sale.order", required=True, ondelete="cascade")
    checkin_date = fields.Datetime(
        "Check In",
        required=True,
        default=fields.Datetime.now,
    )
    checkout_date = fields.Datetime(
        "Check Out",
        readonly=True,
        required=True,
        default=lambda self: self._default_checkout_date(),
    )
    room_line_ids = fields.One2many(
        "hotel.folio.line",
        "folio_id",
        help="Hotel room reservation detail.",
    )
    service_line_ids = fields.One2many(
        "hotel.service.line",
        "folio_id",
        help="Hotel services details provided to "
        "Customer and it will be included in "
        "the main Invoice.",
    )
    hotel_policy = fields.Selection(
        [
            ("prepaid", "On Booking"),
            ("manual", "On Check In"),
            ("picking", "On Checkout"),
        ],
        default="manual",
        help="Hotel policy for payment that "
        "either the guest has to pay at "
        "booking time or check-in "
        "check-out time.",
    )
    duration = fields.Float(
        "Duration in Days",
        help="Number of days which will automatically "
        "count from the check-in and check-out date. ",
    )
    hotel_invoice_id = fields.Many2one("account.move", "Invoice", copy=False)
    duration_dummy = fields.Float()

    @api.constrains("room_line_ids")
    def _check_duplicate_folio_room_line(self):
        """
        Prevent duplicate room bookings for the same product within overlapping dates.
        """
        if self.env.context.get("hotel_v19_import"):
            return
        for rec in self:
            room_lines = rec.room_line_ids.filtered(lambda line: line.state != "cancel")
            if not room_lines:
                continue

            # Group room lines by product_id
            grouped = defaultdict(list)
            for line in room_lines:
                grouped[line.product_id.id].append(line)

            # Check for overlapping bookings within each product
            for product_lines in grouped.values():
                sorted_lines = sorted(product_lines, key=lambda line: line.checkin_date)

                for current, nxt in pairwise(sorted_lines):
                    if current.checkout_date > nxt.checkin_date:
                        raise ValidationError(
                            self.env._(
                                """Room Duplicate Exceeded!
                                You cannot book the same room '%s'
                                twice with overlapping dates.""",
                                current.product_id.display_name,
                            )
                        )

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            vals.setdefault("name", sequence.next_by_code("hotel.folio"))
        return super().create(vals_list)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel folio as well
        ---------------------------------------------------------------
        @param self: object pointer
        """
        if self.partner_id:
            self.update(
                {
                    "partner_invoice_id": self.partner_id.id,
                    "partner_shipping_id": self.partner_id.id,
                    "pricelist_id": self.partner_id.property_product_pricelist.id,
                }
            )

    def action_cancel(self):
        """Cancel the sales orders (and their draft invoices) and free the
        rooms booked on the folios."""
        for rec in self:
            if not rec.order_id:
                raise UserError(rec.env._("Order id is not available"))
        products = self.room_line_ids.product_id
        if products:
            rooms = self.env["hotel.room"].search([("product_id", "in", products.ids)])
            rooms.write({"isroom": True, "status": "available"})
        return self.order_id.action_cancel()

    def action_confirm(self):
        """Confirm through the standard sale flow (deliveries, locking,
        project/analytic generation, confirmation date)."""
        return self.order_id.action_confirm()

    def action_create_invoice(self):
        """Open the standard "Create invoice" wizard on the folios' orders;
        the invoice is linked back to the folio (see account.move)."""
        self.room_line_ids.product_id.write({"isroom": True})
        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale.action_view_sale_advance_payment_inv"
        )
        action["context"] = {
            "active_model": "sale.order",
            "active_ids": self.order_id.ids,
            "active_id": self.order_id[:1].id,
            "folio_id": self[:1].id,
        }
        return action

    def action_cancel_draft(self):
        """Reset cancelled folios to quotation."""
        return self.order_id.action_draft()
