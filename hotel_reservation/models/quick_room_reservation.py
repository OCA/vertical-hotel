from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class QuickRoomReservation(models.TransientModel):
    _name = "quick.room.reservation"
    _description = "Quick Room Reservation"

    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True
    )
    check_in = fields.Datetime("Check In", required=True)
    check_out = fields.Datetime("Check Out", required=True)
    room_id = fields.Many2one("hotel.room", "Room", required=True)
    warehouse_id = fields.Many2one("stock.warehouse", "Hotel", required=True)
    pricelist_id = fields.Many2one("product.pricelist", "pricelist")
    partner_invoice_id = fields.Many2one(
        "res.partner", "Invoice Address", required=True
    )
    partner_order_id = fields.Many2one(
        "res.partner", "Ordering Contact", required=True
    )
    partner_shipping_id = fields.Many2one(
        "res.partner", "Delivery Address", required=True
    )
    adults = fields.Integer("Adults", size=64)

    @api.onchange("check_out", "check_in")
    def on_change_check_out(self):
        """
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        if self.check_out and self.check_in:
            if self.check_out < self.check_in:
                raise ValidationError(
                    _(
                        "Checkout date should be greater \
                                         than Checkin date."
                    )
                )

    @api.onchange("partner_id")
    def onchange_partner_id_res(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        if not self.partner_id:
            self.partner_invoice_id = False
            self.partner_shipping_id = False
            self.partner_order_id = False
        else:
            addr = self.partner_id.address_get(
                ["delivery", "invoice", "contact"]
            )
            self.partner_invoice_id = addr["invoice"]
            self.partner_order_id = addr["contact"]
            self.partner_shipping_id = addr["delivery"]
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(QuickRoomReservation, self).default_get(fields)
        if self._context:
            keys = self._context.keys()
            if "date" in keys:
                res.update({"check_in": self._context["date"]})
            if "room_id" in keys:
                roomid = self._context["room_id"]
                res.update({"room_id": int(roomid)})
        return res

    @api.multi
    def room_reserve(self):
        """
        This method create a new record for hotel.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel reservation.
        """
        hotel_res_obj = self.env["hotel.reservation"]
        for res in self:
            rec = hotel_res_obj.create(
                {
                    "partner_id": res.partner_id.id,
                    "partner_invoice_id": res.partner_invoice_id.id,
                    "partner_order_id": res.partner_order_id.id,
                    "partner_shipping_id": res.partner_shipping_id.id,
                    "checkin": res.check_in,
                    "checkout": res.check_out,
                    "warehouse_id": res.warehouse_id.id,
                    "pricelist_id": res.pricelist_id.id,
                    "adults": res.adults,
                    "reservation_line": [
                        (
                            0,
                            0,
                            {
                                "reserve": [(6, 0, [res.room_id.id])],
                                "name": (
                                    res.room_id and res.room_id.name or ""
                                ),
                            },
                        )
                    ],
                }
            )
        return rec
