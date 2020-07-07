# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.fields import Datetime
from odoo.tests import common


class TestReservationFlow(common.TransactionCase):
    def setUp(self):
        super(TestReservationFlow, self).setUp()
        self.room_0 = self.env.ref("hotel.hotel_room_0")
        self.room_1 = self.env.ref("hotel.hotel_room_1")
        self.partner_1 = self.env.ref("base.res_partner_2")
        self.partner_2 = self.env.ref("base.res_partner_3")
        self.pricelist = self.env.ref("product.list0")

        today = datetime.now()
        self.tomorrow = today + timedelta(days=1)
        self.next_week = today + timedelta(days=7)

    def test_room_capacity_exceeded_raises_validation_error(self):
        # todo creation should pass in draft state
        with self.assertRaises(ValidationError):
            self.env["hotel.reservation"].create(
                {
                    "partner_id": self.partner_1.id,
                    "pricelist_id": self.pricelist.id,
                    "checkin": Datetime.to_string(self.tomorrow),
                    "checkout": Datetime.to_string(self.next_week),
                    "adults": 2,
                    "children": 1,
                }
            )

    def test_book_busy_room_raises_error(self):
        Reservation = self.env["hotel.reservation"]

        reservation_2 = Reservation.create(
            {
                "partner_id": self.partner_1.id,
                "pricelist_id": self.pricelist.id,
                "checkin": Datetime.to_string(self.tomorrow),
                "checkout": Datetime.to_string(self.next_week),
                "adults": 2,
                "reservation_line": [
                    (0, 0, {"reserve": [(6, 0, [self.room_0.id])]})
                ],
            }
        )
        reservation_2.confirmed_reservation()

        reservation_2 = Reservation.create(
            {
                "partner_id": self.partner_2.id,
                "pricelist_id": self.pricelist.id,
                "checkin": Datetime.to_string(self.tomorrow),
                "checkout": Datetime.to_string(self.next_week),
                "adults": 2,
                "reservation_line": [
                    (0, 0, {"reserve": [(6, 0, [self.room_0.id])]})
                ],
            }
        )
        with self.assertRaises(ValidationError):
            reservation_2.confirmed_reservation()

    def test_complete_flow(self):
        Reservation = self.env["hotel.reservation"]
        ReservationLine = self.env["hotel_reservation.line"]

        line_1 = ReservationLine.create(
            {"reserve": [(6, 0, [self.room_0.id])]}
        )
        line_2 = ReservationLine.create(
            {"reserve": [(6, 0, [self.room_1.id])]}
        )

        reservation = Reservation.create(
            {
                "partner_id": self.partner_1.id,
                "pricelist_id": self.pricelist.id,
                "checkin": Datetime.to_string(self.tomorrow),
                "checkout": Datetime.to_string(self.next_week),
                "adults": 2,
                "children": 1,
                "reservation_line": [(6, 0, [line_1.id, line_2.id])],
            }
        )
        # todo partner_invoice_id should be required to pass reservation to
        #  state confirm
        reservation.onchange_partner_id()
        self.assertEquals(
            reservation.partner_id, reservation.partner_invoice_id
        )

        reservation.confirmed_reservation()
        self.assertEquals(reservation.state, "confirm")

        reservation.create_folio()
        self.assertEquals(reservation.state, "done")

        folio = reservation.folio_id

        self.assertEquals(len(folio.room_lines), 2)
        self.assertEquals(folio.state, "draft")
        self.assertEquals(folio.invoice_status, "no")
        self.assertFalse(folio.invoice_ids)

        room_price = (self.room_0.list_price + self.room_1.list_price) * 7
        folio_room_price = sum(folio.room_lines.mapped("price_total"))
        self.assertEquals(folio_room_price, room_price)

        service_checkin = datetime.today() + timedelta(days=3)
        service_checkout = datetime.today() + timedelta(days=5)
        product = self.env.ref("hotel.hotel_service_1")
        service_line = self.env["hotel.service.line"].create(
            {
                "folio_id": folio.id,
                "ser_checkin_date": Datetime.to_string(service_checkin),
                "ser_checkout_date": Datetime.to_string(service_checkout),
                "product_id": product.id,
            }
        )
        service_line.product_id_change()

        folio.action_confirm()
        self.assertEquals(folio.state, "sale")
        self.assertEquals(folio.invoice_status, "to invoice")
        self.assertFalse(folio.invoice_ids)

        wiz = self.env["sale.advance.payment.inv"].create(
            {"advance_payment_method": "all"}
        )
        context = self.env.context.copy()
        context.update()
        wiz.with_context(
            {"active_model": "hotel.folio", "active_ids": [folio.id]}
        ).create_invoices()
        self.assertEquals(folio.state, "sale")
        self.assertEquals(folio.invoice_status, "invoiced")

        invoice = folio.invoice_ids
        self.assertTrue(bool(invoice))

        invoice_total = room_price + service_line.price_total
        self.assertEquals(invoice.amount_total, invoice_total)
