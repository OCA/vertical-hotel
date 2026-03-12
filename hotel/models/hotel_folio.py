# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import timedelta

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
    _inherits = {"sale.order": "order_id"}
    _rec_name = "order_id"

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.order_id.name or rec.name or ""

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        args += [("name", operator, name)]
        folio = self._search(args, limit=100)
        return folio

    @api.model
    def _get_checkin_date(self):
        self.env.context.get("tz") or self.env.user.partner_id.tz or "UTC"
        checkin_date = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        return fields.Datetime.to_string(checkin_date)

    @api.model
    def _get_checkout_date(self):
        self.env.context.get("tz") or self.env.user.partner_id.tz or "UTC"
        checkout_date = fields.Datetime.context_timestamp(
            self, fields.Datetime.now() + timedelta(days=1)
        )
        return fields.Datetime.to_string(checkout_date)

    name = fields.Char("Folio Number", index=True, default="New")
    order_id = fields.Many2one("sale.order", "Order", required=True, ondelete="cascade")
    checkin_date = fields.Datetime(
        "Check In",
        required=True,
        default=lambda self: self._get_checkin_date(),
    )
    checkout_date = fields.Datetime(
        "Check Out",
        readonly=True,
        required=True,
        default=lambda self: self._get_checkout_date(),
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

                for current, nxt in zip(sorted_lines, sorted_lines[1:], strict=False):
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
        """
        @param self: object pointer
        """
        hotel_room_obj = self.env["hotel.room"]
        for rec in self:
            if not rec.order_id:
                raise UserError(rec.env._("Order id is not available"))

            products = rec.room_line_ids.mapped("product_id")
            if products:
                rooms = hotel_room_obj.search([("product_id", "in", products.ids)])
                if rooms:
                    rooms.write({"isroom": True, "status": "available"})

            rec.invoice_ids.button_cancel()
        return self.mapped("order_id").action_cancel()

    def action_confirm(self):
        for order in self.order_id:
            order.state = "sale"
            order.invoice_status = "to invoice"
            if not order.project_account_id:
                if order.order_line.filtered(
                    lambda line: line.product_id.invoice_policy == "cost"
                ):
                    order._create_analytic_account()
            config_parameter_obj = self.env["ir.config_parameter"]
            if config_parameter_obj.sudo().get_param("sale.auto_done_setting"):
                self.order_id.action_done()

    def action_cancel_draft(self):
        """
        @param self: object pointer
        """
        order_line_recs = self.env["sale.order.line"].search(
            [("order_id", "in", self.ids), ("state", "=", "cancel")]
        )
        self.write({"state": "draft", "invoice_ids": []})
        order_line_recs.write(
            {
                "invoiced": False,
                "state": "draft",
                "invoice_lines": [(6, 0, [])],
            }
        )
