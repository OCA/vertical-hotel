# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ReportHotelReservationStatus(models.Model):
    _name = "report.hotel.reservation.status"
    _description = "Reservation By State"
    _auto = False

    reservation_no = fields.Char(readonly=True)
    no_of_reservation = fields.Integer("Reservation", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("done", "Done"),
            ("cancel", "Cancel"),
        ],
        readonly=True,
    )

    def init(self):
        """
        This method is for initialization for report hotel reservation
        status Module.
        @param self: The object pointer
        @param cr: database cursor
        """
        self.env.cr.execute(
            """
            create or replace view report_hotel_reservation_status as (
                select
                    min(c.id) as id,
                    c.reservation_no,
                    c.state,
                    count(*) as no_of_reservation
                from
                    hotel_reservation c
                group by c.state,c.reservation_no
            )"""
        )
