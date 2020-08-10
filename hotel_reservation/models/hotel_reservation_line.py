from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HotelReservationLine(models.Model):
    _name = "hotel_reservation.line"
    _description = "Reservation Line"

    name = fields.Char("Name")
    line_id = fields.Many2one("hotel.reservation")
    reserve = fields.Many2many(
        "hotel.room",
        "hotel_reservation_line_room_rel",
        "hotel_reservation_line_id",
        "room_id",
        domain="[('isroom','=',True),\
                               ('categ_id','=',categ_id)]",
    )
    categ_id = fields.Many2one("hotel.room.type", "Room Type")
    checkin = fields.Datetime(related="line_id.checkin")
    checkout = fields.Datetime(related="line_id.checkout")

    @api.onchange("categ_id")
    def on_change_categ(self):
        """
        When you change categ_id it check checkin and checkout are
        filled or not if not then raise warning
        -----------------------------------------------------------
        @param self: object pointer
        """
        hotel_room_obj = self.env["hotel.room"]
        hotel_room_ids = hotel_room_obj.search(
            [("room_categ_id", "=", self.categ_id.id)]
        )
        room_ids = []
        if not self.line_id.checkin:
            raise ValidationError(
                _(
                    "Before choosing a room,\n You have to \
                                     select a Check in date or a Check out \
                                     date in the reservation form."
                )
            )
        for room in hotel_room_ids:
            assigned = False
            for line in room.room_reservation_line_ids:
                if line.status != "cancel":
                    if (
                        self.line_id.checkin
                        <= line.check_in
                        <= self.line_id.checkout
                    ) or (
                        self.line_id.checkin
                        <= line.check_out
                        <= self.line_id.checkout
                    ):
                        assigned = True
                    elif (
                        line.check_in <= self.line_id.checkin <= line.check_out
                    ) or (
                        line.check_in
                        <= self.line_id.checkout
                        <= line.check_out
                    ):
                        assigned = True
            for rm_line in room.room_line_ids:
                if rm_line.status != "cancel":
                    if (
                        self.line_id.checkin
                        <= rm_line.check_in
                        <= self.line_id.checkout
                    ) or (
                        self.line_id.checkin
                        <= rm_line.check_out
                        <= self.line_id.checkout
                    ):
                        assigned = True
                    elif (
                        rm_line.check_in
                        <= self.line_id.checkin
                        <= rm_line.check_out
                    ) or (
                        rm_line.check_in
                        <= self.line_id.checkout
                        <= rm_line.check_out
                    ):
                        assigned = True
            if not assigned:
                room_ids.append(room.id)
        domain = {"reserve": [("id", "in", room_ids)]}
        return {"domain": domain}

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        hotel_room_reserv_line_obj = self.env["hotel.room.reservation.line"]
        for reserv_rec in self:
            for rec in reserv_rec.reserve:
                hres_arg = [
                    ("room_id", "=", rec.id),
                    ("reservation_id", "=", reserv_rec.line_id.id),
                ]
                myobj = hotel_room_reserv_line_obj.search(hres_arg)
                if myobj.ids:
                    rec.write({"isroom": True, "status": "available"})
                    myobj.unlink()
        return super(HotelReservationLine, self).unlink()
