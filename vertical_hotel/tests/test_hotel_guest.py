# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHotelGuest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.booker = cls.env["res.partner"].create({"name": "Guest Booker"})
        room_type = cls.env["hotel.room.type"].create({"name": "Guest Test Type"})
        cls.room = cls.env["hotel.room"].create(
            {"name": "GT-101", "capacity": 2, "room_categ_id": room_type.id}
        )

    def _folio(self, guests=()):
        checkin = fields.Datetime.now() + timedelta(days=2)
        checkout = checkin + timedelta(days=1)
        return self.env["hotel.folio"].create(
            {
                "partner_id": self.booker.id,
                "checkin_date": checkin,
                "checkout_date": checkout,
                "room_line_ids": [
                    Command.create(
                        {
                            "product_id": self.room.product_id.id,
                            "checkin_date": checkin,
                            "checkout_date": checkout,
                            "product_uom_qty": 1,
                        }
                    )
                ],
                "guest_ids": [
                    Command.create({"name": name, "guest_type": guest_type})
                    for name, guest_type in guests
                ],
            }
        )

    def test_guest_counts_and_contacts(self):
        folio = self._folio([("Priya", "adult"), ("Aarav", "child")])
        self.assertEqual((folio.adults, folio.children, folio.total_guest), (2, 1, 3))
        self.assertEqual(folio.room_capacity, 2)
        # every guest is a contact filed under the booker
        self.assertEqual(folio.guest_ids.partner_id.parent_id, self.booker)
        self.assertEqual(set(self.booker.child_ids.mapped("name")), {"Priya", "Aarav"})

    def test_capacity_checked_on_confirm(self):
        folio = self._folio([("Priya", "adult"), ("Aarav", "child")])
        with self.assertRaises(ValidationError):
            folio.action_confirm()
        folio.guest_ids.filtered(lambda g: g.name == "Aarav").unlink()
        folio.action_confirm()
        self.assertEqual(folio.state, "sale")

    def test_order_confirmed_from_folio_only(self):
        folio = self._folio()
        self.assertTrue(folio.order_id.is_folio_order)
        with self.assertRaises(ValidationError):
            folio.order_id.action_confirm()
        folio.action_confirm()
        self.assertEqual(folio.order_id.state, "sale")

    def test_booker_change_moves_guests(self):
        folio = self._folio([("Priya", "adult")])
        new_booker = self.env["res.partner"].create({"name": "New Booker"})
        folio.partner_id = new_booker
        self.assertEqual(folio.guest_ids.partner_id.parent_id, new_booker)

    def test_removing_guest_removes_contact(self):
        folio = self._folio([("Temporary", "adult")])
        contact = folio.guest_ids.partner_id
        folio.guest_ids.unlink()
        self.assertFalse(contact.exists())
        self.assertEqual(folio.adults, 1)
