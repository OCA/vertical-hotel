# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command

# Check-in time proposed when booking a free day of the reservation summary.
DEFAULT_CHECKIN_TIME = time(12, 0)


class QuickRoomReservation(models.TransientModel):
    _name = "quick.room.reservation"
    _description = "Quick Room Reservation"

    partner_id = fields.Many2one("res.partner", "Customer", required=True)
    check_in = fields.Datetime(required=True)
    check_out = fields.Datetime(required=True)
    room_id = fields.Many2one("hotel.room", required=True)
    company_id = fields.Many2one(
        "res.company", "Hotel", required=True, default=lambda self: self.env.company
    )
    pricelist_id = fields.Many2one("product.pricelist", "pricelist")
    # filled from the customer; the customer is used when left empty
    partner_invoice_id = fields.Many2one("res.partner", "Invoice Address")
    partner_order_id = fields.Many2one("res.partner", "Ordering Contact")
    partner_shipping_id = fields.Many2one("res.partner", "Delivery Address")
    adults = fields.Integer(default=1)

    @api.constrains("check_in", "check_out")
    def _check_dates(self):
        """
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        for rec in self:
            if rec.check_in and rec.check_out and rec.check_out <= rec.check_in:
                raise ValidationError(
                    self.env._("Checkout date should be greater than Checkin date.")
                )

    @api.onchange("partner_id")
    def _onchange_partner_id_res(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        if not self.partner_id:
            self.update(
                {
                    "partner_invoice_id": False,
                    "partner_shipping_id": False,
                    "partner_order_id": False,
                }
            )
        else:
            addr = self.partner_id.address_get(["delivery", "invoice", "contact"])
            self.update(
                {
                    "partner_invoice_id": addr["invoice"],
                    "partner_shipping_id": addr["delivery"],
                    "partner_order_id": addr["contact"],
                    "pricelist_id": self.partner_id.property_product_pricelist.id,
                }
            )

    def _day_to_checkin(self, day):
        """A day of the summary (``YYYY-MM-DD``, user's timezone) as the
        UTC check-in datetime, at DEFAULT_CHECKIN_TIME."""
        tz = ZoneInfo(self.env.context.get("tz") or self.env.user.tz or "UTC")
        local = datetime.combine(
            fields.Date.to_date(day), DEFAULT_CHECKIN_TIME, tzinfo=tz
        )
        return local.astimezone(UTC).replace(tzinfo=None)

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        res = super().default_get(fields)
        context = self.env.context
        day = context.get("quick_reservation_date")
        if day:
            check_in = self._day_to_checkin(day)
            res.update(
                {"check_in": check_in, "check_out": check_in + timedelta(days=1)}
            )
        elif "date" in context:
            res.update({"check_in": context["date"]})
        if "room_id" in context:
            res.update({"room_id": int(context["room_id"])})
        return res

    def _get_pricelist(self):
        """The chosen pricelist, else the customer's, else the hotel's first."""
        self.ensure_one()
        pricelist = (
            self.pricelist_id
            or self.partner_id.property_product_pricelist
            or self.env["product.pricelist"].search(
                [("company_id", "in", [False, self.company_id.id])], limit=1
            )
        )
        if not pricelist:
            raise UserError(self.env._("Please set a pricelist for the reservation."))
        return pricelist

    def room_reserve(self):
        """
        This method create a new record for hotel.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: action opening the new hotel reservation.
        """
        reservations = self.env["hotel.reservation"]
        for res in self:
            reservations |= reservations.create(
                {
                    "partner_id": res.partner_id.id,
                    "partner_invoice_id": (res.partner_invoice_id or res.partner_id).id,
                    "partner_order_id": (res.partner_order_id or res.partner_id).id,
                    "partner_shipping_id": (
                        res.partner_shipping_id or res.partner_id
                    ).id,
                    "checkin": res.check_in,
                    "checkout": res.check_out,
                    "company_id": res.company_id.id,
                    "pricelist_id": res._get_pricelist().id,
                    "adults": res.adults,
                    "reservation_line": [
                        Command.create(
                            {
                                "categ_id": res.room_id.room_categ_id.id,
                                "reserve": [Command.set(res.room_id.ids)],
                                "name": res.room_id.name or " ",
                            }
                        )
                    ],
                }
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": "hotel.reservation",
            "res_id": reservations[:1].id,
            "views": [
                (
                    self.env.ref("hotel_reservation.view_hotel_reservation_form").id,
                    "form",
                )
            ],
            "target": "current",
        }
