# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.tests import common


class TestHotel(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.hotel_folio_obj = self.env["hotel.folio"]
        self.hotel_folio_line = self.env["hotel.folio.line"]
        self.warehouse = self.env.ref("stock.warehouse0")
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        cur_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.checkin_date = datetime.now() + timedelta(days=1)
        self.checkout_date = self.checkin_date + timedelta(days=2)

        self.price_list = self.env["product.pricelist"].create(
            {
                "name": "Test Pricelist",
                "currency_id": self.env.ref("base.USD").id,
            }
        )
        self.hotel_folio = self.hotel_folio_obj.create(
            {
                "name": "Folio/00001",
                "date_order": cur_date,
                "warehouse_id": self.warehouse.id,
                "invoice_status": "no",
                "pricelist_id": self.price_list.id,
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "state": "draft",
            }
        )

    def _create_room(self, name):
        room_type = self.env["hotel.room.type"].create({"name": "Test Room Type"})
        return self.env["hotel.room"].create(
            {
                "name": name,
                "list_price": 100.0,
                "capacity": 2,
                "isroom": True,
                "room_categ_id": room_type.id,
            }
        )

    def test_folio_line_onchange_product_id(self):
        """Folio line onchange fills the sale.order.line fields (v19 names)."""
        room = self._create_room("Test Room")
        folio_line = self.hotel_folio_line.create(
            {
                "folio_id": self.hotel_folio.id,
                "product_id": room.product_id.id,
                "checkin_date": self.checkin_date,
                "checkout_date": self.checkout_date,
                "product_uom_qty": 1.0,
            }
        )

        self.assertFalse(folio_line._onchange_product_id_warning())
        self.assertEqual(folio_line.name, room.product_id.name)
        self.assertEqual(folio_line.product_uom_id, room.product_id.uom_id)
        self.assertEqual(folio_line.price_unit, room.product_id.list_price)
        self.assertEqual(
            folio_line.tax_ids,
            room.product_id.taxes_id.filtered(
                lambda tax: tax.company_id == self.hotel_folio.company_id
            ),
        )

    def test_folio_line_onchange_product_id_warning(self):
        """A product warning message is returned to the user."""
        room = self._create_room("Warned Room")
        room.product_id.sale_line_warn_msg = "Room under maintenance"
        folio_line = self.hotel_folio_line.create(
            {
                "folio_id": self.hotel_folio.id,
                "product_id": room.product_id.id,
                "checkin_date": self.checkin_date,
                "checkout_date": self.checkout_date,
                "product_uom_qty": 1.0,
            }
        )

        result = folio_line._onchange_product_id_warning()
        self.assertEqual(result["warning"]["message"], "Room under maintenance")
        self.assertEqual(folio_line.product_id, room.product_id)

    def test_service_line_onchange_product_id(self):
        """Service line onchange fills the sale.order.line fields (v19 names)."""
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
        self.assertEqual(
            service_line.tax_ids,
            service.taxes_id.filtered(
                lambda tax: tax.company_id == self.hotel_folio.company_id
            ),
        )

    def test_service_line_onchange_product_id_warning(self):
        """A product warning message is returned to the user."""
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

    def _create_sale_tax(self, name, company):
        tax_group_id = self.env["account.tax.group"].create(
            {"name": name, "company_id": company.id}
        )
        return self.env["account.tax"].create(
            {
                "name": name,
                "amount": 10.0,
                "type_tax_use": "sale",
                "company_id": company.id,
                "tax_group_id": tax_group_id.id,
            }
        )

    def _create_multi_company_taxes(self):
        """Return a tax of the folio company and one of another company."""
        other_company_id = self.env["res.company"].create(
            {
                "name": "Other Hotel",
                "country_id": self.hotel_folio.company_id.country_id.id,
            }
        )
        own_tax_id = self._create_sale_tax("Own Tax", self.hotel_folio.company_id)
        other_tax_id = self._create_sale_tax("Other Tax", other_company_id)
        return own_tax_id, other_tax_id

    def test_line_onchange_product_id_company_taxes(self):
        """Only the taxes of the folio company are set on the lines."""
        own_tax_id, other_tax_id = self._create_multi_company_taxes()
        room = self._create_room("Shared Room")
        service_id = self.env["product.product"].create(
            {"name": "Shared Service", "list_price": 50.0, "isservice": True}
        )
        (room.product_id | service_id).taxes_id = own_tax_id | other_tax_id
        folio_line_id = self.hotel_folio_line.create(
            {
                "folio_id": self.hotel_folio.id,
                "product_id": room.product_id.id,
                "checkin_date": self.checkin_date,
                "checkout_date": self.checkout_date,
            }
        )
        service_line_id = self.env["hotel.service.line"].create(
            {
                "folio_id": self.hotel_folio.id,
                "product_id": service_id.id,
                "ser_checkin_date": self.checkin_date,
                "ser_checkout_date": self.checkout_date,
            }
        )

        folio_line_id._onchange_product_id_warning()
        service_line_id._onchange_product_id_warning()
        self.assertEqual(folio_line_id.tax_ids, own_tax_id)
        self.assertEqual(service_line_id.tax_ids, own_tax_id)

    def test_line_onchange_product_id_fiscal_position(self):
        """The product taxes are mapped through the folio fiscal position."""
        own_tax_id, other_tax_id = self._create_multi_company_taxes()
        fiscal_position_id = self.env["account.fiscal.position"].create(
            {"name": "Export"}
        )
        export_tax_id = self._create_sale_tax("Export Tax", self.hotel_folio.company_id)
        export_tax_id.write(
            {
                "fiscal_position_ids": [(6, 0, fiscal_position_id.ids)],
                "original_tax_ids": [(6, 0, own_tax_id.ids)],
            }
        )
        self.hotel_folio.fiscal_position_id = fiscal_position_id
        room = self._create_room("Export Room")
        room.product_id.taxes_id = own_tax_id | other_tax_id
        folio_line_id = self.hotel_folio_line.create(
            {
                "folio_id": self.hotel_folio.id,
                "product_id": room.product_id.id,
                "checkin_date": self.checkin_date,
                "checkout_date": self.checkout_date,
            }
        )

        folio_line_id._onchange_product_id_warning()
        self.assertEqual(folio_line_id.tax_ids, export_tax_id)

    def test_search_fetch_from_room(self):
        """from_room context keeps only the rooms free on the given dates."""
        room = self._create_room("Searchable Room")
        product_obj = self.env["product.product"].with_context(
            from_room=True,
            checkin_date=self.checkin_date.strftime("%Y-%m-%d %H:%M:%S"),
            checkout_date=self.checkout_date.strftime("%Y-%m-%d %H:%M:%S"),
        )

        found = product_obj.name_search("Searchable Room")
        self.assertIn(room.product_id.id, [prod[0] for prod in found])

        self.env["folio.room.line"].create(
            {
                "room_id": room.id,
                "check_in": self.checkin_date,
                "check_out": self.checkout_date,
                "folio_id": self.hotel_folio.id,
            }
        )

        found = product_obj.name_search("Searchable Room")
        self.assertNotIn(room.product_id.id, [prod[0] for prod in found])

    def test_confirm_sale(self):
        self.hotel_folio.action_confirm()
        self.assertEqual(self.hotel_folio.state == "sale", True)

    def test_folio_cancel(self):
        self.hotel_folio.action_cancel()
        self.assertEqual(self.hotel_folio.state == "cancel", True)

    def test_folio_set_to_draft(self):
        self.hotel_folio.action_cancel_draft()
        self.assertEqual(self.hotel_folio.state == "draft", True)
