from odoo import api, fields, models


class HotelFolio(models.Model):
    _inherit = "hotel.folio"
    _order = "reservation_id desc"

    reservation_id = fields.Many2one(
        "hotel.reservation", string="Reservation Id"
    )

    def write(self, vals):
        context = dict(self._context)
        if not context:
            context = {}
        context.update({"from_reservation": True})
        res = super(HotelFolio, self).write(vals)
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        for folio_obj in self:
            if folio_obj.reservation_id:
                for reservation in folio_obj.reservation_id:
                    reservation_obj = reservation_line_obj.search(
                        [("reservation_id", "=", reservation.id)]
                    )
                    if len(reservation_obj) == 1:
                        for line_id in reservation.reservation_line:
                            line_id = line_id.reserve
                            for room_id in line_id:
                                vals = {
                                    "room_id": room_id.id,
                                    "check_in": folio_obj.checkin_date,
                                    "check_out": folio_obj.checkout_date,
                                    "state": "assigned",
                                    "reservation_id": reservation.id,
                                }
                                reservation_obj.write(vals)
        return res


class HotelFolioLine(models.Model):
    _inherit = "hotel.folio.line"

    @api.onchange("checkin_date", "checkout_date")
    def on_change_checkout(self):
        res = super(HotelFolioLine, self).on_change_checkout()
        hotel_room_obj = self.env["hotel.room"]
        avail_prod_ids = []
        hotel_room_ids = hotel_room_obj.search([])
        for room in hotel_room_ids:
            assigned = False
            for line in room.room_reservation_line_ids:
                if line.status != "cancel":
                    if (
                        self.checkin_date
                        <= line.check_in
                        <= self.checkout_date
                    ) or (
                        self.checkin_date
                        <= line.check_out
                        <= self.checkout_date
                    ):
                        assigned = True
                    elif (
                        line.check_in <= self.checkin_date <= line.check_out
                    ) or (
                        line.check_in <= self.checkout_date <= line.check_out
                    ):
                        assigned = True
            if not assigned:
                avail_prod_ids.append(room.product_id.id)
        return res

    @api.multi
    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        Update Hotel Room Reservation line history"""
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        room_obj = self.env["hotel.room"]
        prod_id = vals.get("product_id") or self.product_id.id
        chkin = vals.get("checkin_date") or self.checkin_date
        chkout = vals.get("checkout_date") or self.checkout_date
        is_reserved = self.is_reserved
        if prod_id and is_reserved:
            prod_domain = [("product_id", "=", prod_id)]
            prod_room = room_obj.search(prod_domain, limit=1)
            if self.product_id and self.checkin_date and self.checkout_date:
                old_prd_domain = [("product_id", "=", self.product_id.id)]
                old_prod_room = room_obj.search(old_prd_domain, limit=1)
                if prod_room and old_prod_room:
                    # Check for existing room lines.
                    srch_rmline = [
                        ("room_id", "=", old_prod_room.id),
                        ("check_in", "=", self.checkin_date),
                        ("check_out", "=", self.checkout_date),
                    ]
                    rm_lines = reservation_line_obj.search(srch_rmline)
                    if rm_lines:
                        rm_line_vals = {
                            "room_id": prod_room.id,
                            "check_in": chkin,
                            "check_out": chkout,
                        }
                        rm_lines.write(rm_line_vals)
        return super(HotelFolioLine, self).write(vals)
