# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools
from odoo.tools import SQL


class ReportHotelReservationStatus(models.Model):
    """Reservation analysis: one row per reserved room.

    The reservation counters (reservations, adults, children, guests) are
    only on the first row of each reservation, so their sums are right
    whatever the number of rooms; room nights are per room."""

    _name = "report.hotel.reservation.status"
    _description = "Reservation Analysis"
    _auto = False
    _order = "checkin desc, reservation_id desc"

    reservation_id = fields.Many2one("hotel.reservation", readonly=True)
    reservation_no = fields.Char(readonly=True)
    partner_id = fields.Many2one("res.partner", "Guest", readonly=True)
    company_id = fields.Many2one("res.company", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("done", "Done"),
            ("cancel", "Cancel"),
        ],
        readonly=True,
    )
    date_order = fields.Datetime("Date Ordered", readonly=True)
    checkin = fields.Datetime("Check-In", readonly=True)
    checkout = fields.Datetime("Check-Out", readonly=True)
    room_id = fields.Many2one("hotel.room", readonly=True)
    room_type_id = fields.Many2one("hotel.room.type", readonly=True)
    room_nights = fields.Integer(readonly=True)
    no_of_reservation = fields.Integer("Reservations", readonly=True)
    adults = fields.Integer(readonly=True)
    children = fields.Integer(readonly=True)
    guests = fields.Integer(readonly=True)

    def init(self):
        """
        Initialization for report hotel reservation status module.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                WITH booked AS (
                    SELECT
                        r.id AS reservation_id,
                        line.id AS line_id,
                        rel.room_id,
                        row_number() OVER (
                            PARTITION BY r.id ORDER BY line.id, rel.room_id
                        ) AS position
                    FROM hotel_reservation r
                    LEFT JOIN hotel_reservation_line line ON line.line_id = r.id
                    LEFT JOIN hotel_reservation_line_room_rel rel
                        ON rel.hotel_reservation_line_id = line.id
                )
                SELECT
                    row_number() OVER (
                        ORDER BY booked.reservation_id, booked.line_id, booked.room_id
                    ) AS id,
                    r.id AS reservation_id,
                    r.reservation_no,
                    r.partner_id,
                    r.company_id,
                    r.state,
                    r.date_order,
                    r.checkin,
                    r.checkout,
                    booked.room_id,
                    COALESCE(line.categ_id, room.room_categ_id) AS room_type_id,
                    CASE WHEN booked.room_id IS NULL THEN 0
                        ELSE GREATEST(r.checkout::date - r.checkin::date, 1)
                    END AS room_nights,
                    CASE WHEN booked.position = 1 THEN 1 ELSE 0 END
                        AS no_of_reservation,
                    CASE WHEN booked.position = 1 THEN COALESCE(r.adults, 0)
                        ELSE 0 END AS adults,
                    CASE WHEN booked.position = 1 THEN COALESCE(r.children, 0)
                        ELSE 0 END AS children,
                    CASE WHEN booked.position = 1
                        THEN COALESCE(r.adults, 0) + COALESCE(r.children, 0)
                        ELSE 0 END AS guests
                FROM booked
                JOIN hotel_reservation r ON r.id = booked.reservation_id
                LEFT JOIN hotel_reservation_line line ON line.id = booked.line_id
                LEFT JOIN hotel_room room ON room.id = booked.room_id
            )"""
        self.env.cr.execute(SQL(query, SQL.identifier(self._table)))
