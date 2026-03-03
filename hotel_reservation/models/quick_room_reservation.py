# Copyright (C) 2022-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class QuickRoomReservation(models.TransientModel):
    _name = "quick.room.reservation"
    _description = "Quick Room Reservation"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=True,
    )
    check_in = fields.Datetime(
        required=True,
    )
    check_out = fields.Datetime(
        required=True,
    )
    room_id = fields.Many2one(
        comodel_name="hotel.room",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Hotel",
        required=True,
    )
    pricelist_id = fields.Many2one(
        comodel_name="product.pricelist",
    )
    partner_invoice_id = fields.Many2one(
        comodel_name="res.partner",
        string="Invoice Address",
        required=True,
    )
    partner_order_id = fields.Many2one(
        comodel_name="res.partner",
        string="Ordering Contact",
        required=True,
    )
    partner_shipping_id = fields.Many2one(
        comodel_name="res.partner",
        string="Delivery Address",
        required=True,
    )
    adults = fields.Integer()

    @api.onchange("check_out", "check_in")
    def _on_change_check_out(self):
        """
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        if (self.check_out and self.check_in) and (self.check_out < self.check_in):
            raise ValidationError(
                _("Checkout date should be greater than Checkin date.")
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

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        keys = self._context.keys()
        if "date" in keys:
            res.update({"check_in": self._context["date"]})
        if "room_id" in keys:
            room_id = self._context["room_id"]
            res.update({"room_id": int(room_id)})
        return res

    def room_reserve(self):
        Reservation = self.env["hotel.reservation"]
        for reservation in self:
            res = Reservation.create(
                {
                    "partner_id": reservation.partner_id.id,
                    "partner_invoice_id": reservation.partner_invoice_id.id,
                    "partner_order_id": reservation.partner_order_id.id,
                    "partner_shipping_id": reservation.partner_shipping_id.id,
                    "checkin": reservation.check_in,
                    "checkout": reservation.check_out,
                    "company_id": reservation.company_id.id,
                    "pricelist_id": reservation.pricelist_id.id,
                    "adults": reservation.adults,
                    "reservation_line": [
                        (
                            0,
                            0,
                            {
                                "reserve": [(6, 0, reservation.room_id.ids)],
                                "name": reservation.room_id.name or " ",
                            },
                        )
                    ],
                }
            )
        return res
