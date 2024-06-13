# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HotelFolio(models.Model):
    _inherit = "hotel.folio"

    hotel_reservation_orders_ids = fields.Many2many(
        "hotel.reservation.order",
        "hotel_res_rel",
        "hotel_folio_id",
        "reste_id",
        "Reservation Orders",
    )
    hotel_restaurant_orders_ids = fields.Many2many(
        "hotel.restaurant.order",
        "hotel_res_resv",
        "hfolio_id",
        "reserves_id",
        "Restaurant Orders",
    )
