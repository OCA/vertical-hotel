# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestReservationGuestContacts(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        room_type = cls.env["hotel.room.type"].create({"name": "GuestTest Type"})
        cls.room = cls.env["hotel.room"].create(
            {
                "name": "GuestTest-101",
                "room_categ_id": room_type.id,
                "capacity": 4,
                "list_price": 100.0,
            }
        )
        cls.booker = cls.env["res.partner"].create({"name": "GuestTest Booker"})
        cls.pricelist = cls.env["product.pricelist"].search([], limit=1) or cls.env[
            "product.pricelist"
        ].create({"name": "GuestTest Pricelist"})
        cls.checkin = fields.Datetime.now() + timedelta(days=30)

    def _reservation(self, guests):
        return self.env["hotel.reservation"].create(
            {
                "partner_id": self.booker.id,
                "partner_invoice_id": self.booker.id,
                "partner_order_id": self.booker.id,
                "partner_shipping_id": self.booker.id,
                "pricelist_id": self.pricelist.id,
                "checkin": self.checkin,
                "checkout": self.checkin + timedelta(days=2),
                "reservation_line": [
                    Command.create(
                        {
                            "categ_id": self.room.room_categ_id.id,
                            "reserve": [Command.set(self.room.ids)],
                        }
                    )
                ],
                "guest_ids": [
                    Command.create({"name": name, "guest_type": guest_type})
                    for name, guest_type in guests
                ],
            }
        )

    def test_folio_reuses_the_reservation_guest_contacts(self):
        reservation = self._reservation([("Jainam", "adult"), ("Khushi", "child")])
        self.assertEqual(len(self.booker.child_ids), 2)

        reservation.confirmed_reservation()
        reservation.create_folio()
        folio = reservation.folio_id

        self.assertEqual(folio.guest_ids.partner_id, reservation.guest_ids.partner_id)
        self.assertEqual(
            len(self.booker.child_ids),
            2,
            "creating the folio must not duplicate contacts",
        )
        self.assertEqual(
            sorted(folio.guest_ids.mapped("guest_type")), ["adult", "child"]
        )
        self.assertEqual((folio.adults, folio.children), (2, 1))

    def test_removing_a_folio_guest_keeps_the_shared_contact(self):
        reservation = self._reservation([("Suniti", "adult")])
        reservation.confirmed_reservation()
        reservation.create_folio()
        contact = reservation.guest_ids.partner_id

        reservation.folio_id.guest_ids.unlink()

        self.assertTrue(contact.exists())
        self.assertTrue(contact.active)
        self.assertEqual(reservation.guest_ids.partner_id, contact)

    def test_removing_the_last_guest_line_removes_the_contact(self):
        reservation = self._reservation([("Temporary", "adult")])
        contact = reservation.guest_ids.partner_id

        reservation.guest_ids.unlink()

        self.assertFalse(contact.exists())
