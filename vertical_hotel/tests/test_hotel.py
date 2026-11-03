# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestHotel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.checkin_date = fields.Datetime.now().replace(microsecond=0) + timedelta(
            days=1
        )
        cls.checkout_date = cls.checkin_date + timedelta(days=2)
        cls.room_type = cls.env["hotel.room.type"].create({"name": "Test Room Type"})
        cls.room = cls._create_room("Test Room")
        cls.hotel_folio = cls._create_folio()

    @classmethod
    def _create_room(cls, name, **vals):
        return cls.env["hotel.room"].create(
            {
                "name": name,
                "list_price": 100.0,
                "capacity": 2,
                "isroom": True,
                "room_categ_id": cls.room_type.id,
                **vals,
            }
        )

    @classmethod
    def _create_folio(cls):
        return cls.env["hotel.folio"].create(
            {
                "warehouse_id": cls.warehouse.id,
                "partner_id": cls.partner.id,
                "partner_invoice_id": cls.partner.id,
                "partner_shipping_id": cls.partner.id,
            }
        )

    def _add_room_line(self, folio, room, checkin=None, checkout=None):
        return self.env["hotel.folio.line"].create(
            {
                "folio_id": folio.id,
                "product_id": room.product_id.id,
                "checkin_date": checkin or self.checkin_date,
                "checkout_date": checkout or self.checkout_date,
                "product_uom_qty": 2.0,
            }
        )

    def _available(self, checkin, checkout, name="Test Room"):
        products = (
            self.env["product.product"]
            .with_context(
                from_room=True,
                checkin_date=fields.Datetime.to_string(checkin),
                checkout_date=fields.Datetime.to_string(checkout),
            )
            .name_search(name)
        )
        return [product_id for product_id, __ in products]

    # Folio / lines --------------------------------------------------------

    def test_folio_sequence_and_display_name(self):
        self.assertTrue(self.hotel_folio.name.startswith("Folio/"))
        self.assertEqual(self.hotel_folio.display_name, self.hotel_folio.order_id.name)
        found = self.env["hotel.folio"].name_search(self.hotel_folio.name)
        self.assertIn(self.hotel_folio.id, [folio_id for folio_id, __ in found])

    def test_room_and_service_products_are_services(self):
        self.assertEqual(self.room.type, "service")
        service = self.env["hotel.services"].create(
            {
                "name": "Laundry",
                "service_categ_id": self.env["hotel.service.type"]
                .create({"name": "Cleaning"})
                .id,
            }
        )
        self.assertEqual(service.type, "service")

    def test_folio_line_onchange_product_id(self):
        """Folio line onchange fills the sale.order.line fields."""
        folio_line = self._add_room_line(self.hotel_folio, self.room)
        self.assertFalse(folio_line._onchange_product_id_warning())
        self.assertEqual(folio_line.name, self.room.product_id.name)
        self.assertEqual(folio_line.product_uom_id, self.room.product_id.uom_id)
        self.assertEqual(folio_line.price_unit, self.room.product_id.list_price)
        self.assertEqual(
            folio_line.tax_ids,
            self.room.product_id.taxes_id._filter_taxes_by_company(
                self.hotel_folio.company_id
            ),
        )

    def test_folio_line_onchange_taxes_of_folio_company_only(self):
        """Taxes of other companies are never copied on the line."""
        other_company = self.env["res.company"].create(
            {"name": "Other Hotel Co", "country_id": self.env.ref("base.be").id}
        )
        tax_group = self.env["account.tax.group"].create(
            {"name": "Other group", "company_id": other_company.id}
        )
        other_tax = self.env["account.tax"].create(
            {
                "name": "Other 7%",
                "amount": 7,
                "company_id": other_company.id,
                "tax_group_id": tax_group.id,
            }
        )
        self.room.product_id.taxes_id |= other_tax
        folio_line = self._add_room_line(self.hotel_folio, self.room)
        folio_line._onchange_product_id_warning()
        self.assertNotIn(other_tax, folio_line.tax_ids)

    def test_folio_line_onchange_product_id_warning(self):
        """A product warning message is returned to the user."""
        self.room.product_id.sale_line_warn_msg = "Room under maintenance"
        folio_line = self._add_room_line(self.hotel_folio, self.room)
        result = folio_line._onchange_product_id_warning()
        self.assertEqual(result["warning"]["message"], "Room under maintenance")

    def test_service_line_onchange_product_id(self):
        """Service line onchange fills the sale.order.line fields."""
        service = self.env["product.product"].create(
            {"name": "Test Service", "list_price": 50.0, "isservice": True}
        )
        service_line = self.env["hotel.service.line"].create(
            {
                "folio_id": self.hotel_folio.id,
                "product_id": service.id,
                "product_uom_qty": 1.0,
                "ser_checkin_date": self.checkin_date,
                "ser_checkout_date": self.checkout_date,
            }
        )
        self.assertFalse(service_line._onchange_product_id_warning())
        self.assertEqual(service_line.name, service.name)
        self.assertEqual(service_line.product_uom_id, service.uom_id)
        self.assertEqual(service_line.price_unit, service.list_price)

    def test_service_line_onchange_product_id_warning(self):
        service = self.env["product.product"].create(
            {
                "name": "Warned Service",
                "list_price": 50.0,
                "isservice": True,
                "sale_line_warn_msg": "Service not available",
            }
        )
        service_line = self.env["hotel.service.line"].create(
            {
                "folio_id": self.hotel_folio.id,
                "product_id": service.id,
                "product_uom_qty": 1.0,
            }
        )
        result = service_line._onchange_product_id_warning()
        self.assertEqual(result["warning"]["message"], "Service not available")

    def test_service_line_dates_onchange(self):
        """Only the check-in date set: checkout defaults to it (1 day)."""
        service_line = self.env["hotel.service.line"].new(
            {"ser_checkin_date": self.checkin_date}
        )
        service_line._on_change_checkin_checkout_dates()
        self.assertEqual(service_line.ser_checkout_date, self.checkin_date)
        self.assertEqual(service_line.product_uom_qty, 1)

    # Workflow -------------------------------------------------------------

    def test_confirm_sale(self):
        self._add_room_line(self.hotel_folio, self.room)
        self.hotel_folio.action_confirm()
        self.assertEqual(self.hotel_folio.state, "sale")
        self.assertEqual(self.hotel_folio.invoice_status, "to invoice")
        # rooms are services: no delivery order for a night in a room
        self.assertFalse(self.hotel_folio.order_id.picking_ids)

    def test_folio_cancel_frees_rooms(self):
        self._add_room_line(self.hotel_folio, self.room)
        self.assertEqual(self.room.status, "occupied")
        self.hotel_folio.action_cancel()
        self.assertEqual(self.hotel_folio.state, "cancel")
        self.assertEqual(self.room.status, "available")

    def test_folio_set_to_draft(self):
        self.hotel_folio.action_cancel()
        self.hotel_folio.action_cancel_draft()
        self.assertEqual(self.hotel_folio.state, "draft")

    def test_create_invoice_links_folio(self):
        self._add_room_line(self.hotel_folio, self.room)
        self.hotel_folio.action_confirm()
        action = self.hotel_folio.action_create_invoice()
        wizard = (
            self.env["sale.advance.payment.inv"]
            .with_context(**action["context"])
            .create({})
        )
        self.assertEqual(wizard.sale_order_ids, self.hotel_folio.order_id)
        wizard.create_invoices()
        self.assertTrue(self.hotel_folio.hotel_invoice_id)
        self.assertEqual(self.hotel_folio.invoice_status, "invoiced")

    # Room availability ----------------------------------------------------

    def test_search_fetch_from_room(self):
        """from_room context keeps only the rooms free on the given dates."""
        product = self.room.product_id
        stay = (self.checkin_date, self.checkout_date)
        self.assertIn(product.id, self._available(*stay))
        self._add_room_line(self.hotel_folio, self.room)
        # overlapping stay
        self.assertNotIn(
            product.id,
            self._available(
                self.checkin_date + timedelta(hours=1),
                self.checkout_date + timedelta(days=1),
            ),
        )
        # stay starting when the booked one ends
        self.assertIn(
            product.id,
            self._available(self.checkout_date, self.checkout_date + timedelta(days=1)),
        )
        # a cancelled folio does not block the room
        self.hotel_folio.action_cancel()
        self.assertIn(product.id, self._available(*stay))

    def test_search_fetch_from_room_only_rooms(self):
        """The availability filter never returns non-room products."""
        self.env["product.product"].create({"name": "Test Room Service"})
        found = self._available(self.checkin_date, self.checkout_date, "Test Room")
        self.assertEqual(found, [self.room.product_id.id])

    def test_double_booking_constraint(self):
        self._add_room_line(self.hotel_folio, self.room)
        with self.assertRaises(ValidationError):
            self._add_room_line(
                self.hotel_folio,
                self.room,
                self.checkin_date + timedelta(hours=2),
                self.checkout_date + timedelta(hours=2),
            )

    # Categories -----------------------------------------------------------

    def test_room_type_hierarchical_name_search(self):
        child = self.env["hotel.room.type"].create(
            {"name": "Deluxe", "categ_id": self.room_type.id}
        )
        self.assertEqual(child.display_name, "Test Room Type / Deluxe")
        found = self.env["hotel.room.type"].name_search("Test Room Type / Del")
        self.assertEqual([type_id for type_id, __ in found], [child.id])

    def test_amenity_and_service_type_hierarchical_name_search(self):
        for model, parent_field in (
            ("hotel.room.amenities.type", "amenity_id"),
            ("hotel.service.type", "service_id"),
        ):
            parent = self.env[model].create({"name": "Parent X"})
            child = self.env[model].create({"name": "Child Y", parent_field: parent.id})
            found = self.env[model].name_search("Parent X / Child")
            self.assertEqual([rec_id for rec_id, __ in found], [child.id], model)

    # Report ---------------------------------------------------------------

    def test_report_folio_data(self):
        empty_folio = self._create_folio()
        self._add_room_line(self.hotel_folio, self.room)
        data = self.env["report.vertical_hotel.report_hotel_folio"]._get_folio_data(
            self.checkin_date - timedelta(days=5),
            self.checkout_date + timedelta(days=5),
        )
        rows = {row["name"]: row for row in data if "name" in row}
        self.assertEqual(rows[self.hotel_folio.name]["checkin"], self.checkin_date)
        self.assertEqual(rows[self.hotel_folio.name]["checkout"], self.checkout_date)
        self.assertIn(empty_folio.name, rows)
        self.assertEqual(
            data[-1]["total_amount"],
            sum(row["amount"] for row in rows.values()),
        )

    def test_report_wizard(self):
        # without a document layout, report_action() opens the layout setup
        self.env.company.external_report_layout_id = self.env.ref(
            "web.external_layout_standard"
        )
        wizard = Form(self.env["folio.report.wizard"])
        wizard.date_start = self.checkin_date - timedelta(days=5)
        wizard.date_end = self.checkout_date + timedelta(days=5)
        action = wizard.save().print_report()
        self.assertEqual(action["report_name"], "vertical_hotel.report_hotel_folio")


@tagged("post_install", "-at_install")
class TestHotelSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hotel_user = new_test_user(
            cls.env, login="hotel_user", groups="vertical_hotel.group_hotel_user"
        )
        cls.internal_user = new_test_user(
            cls.env, login="plain_user", groups="base.group_user"
        )

    def test_admin_is_hotel_manager(self):
        self.assertIn(
            self.env.ref("vertical_hotel.group_hotel_manager"),
            self.env.ref("base.user_admin").all_group_ids,
        )

    def test_hotel_user_can_work_with_folios(self):
        folio = (
            self.env["hotel.folio"]
            .with_user(self.hotel_user)
            .create(
                {"partner_id": self.env["res.partner"].create({"name": "Guest"}).id}
            )
        )
        self.assertTrue(folio.name)
        with self.assertRaises(AccessError):
            folio.unlink()

    def test_internal_user_has_no_hotel_access(self):
        with self.assertRaises(AccessError):
            self.env["hotel.folio"].with_user(self.internal_user).search([])
