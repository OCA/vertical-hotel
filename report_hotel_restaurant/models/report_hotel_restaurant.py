# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ReportHotelRestaurantStatus(models.Model):
    _name = "report.hotel.restaurant.status"
    _description = "Reservation By State"
    _auto = False

    reservation_id = fields.Char("Reservation No", readonly=True)
    no_of_reservation_order = fields.Integer("Reservation Order No", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("done", "Done"),
            ("cancel", "Cancel"),
            ("order", "Order Created"),
        ],
        readonly=True,
    )

    def init(self):
        """
        This method is for initialization for report hotel restaurant
        status Module.
        @param self: The object pointer
        @param cr: database cursor
        """
        self.env.cr.execute(
            """
            create or replace view report_hotel_restaurant_status as (
                select
                    min(c.id) as id,
                    c.reservation_id,
                    c.state,
                    count(*) as no_of_reservation_order
                from
                    hotel_restaurant_reservation c
                group by c.state,c.reservation_id
            )"""
        )
