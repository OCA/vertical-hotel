# See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo.tests import common


class TestHotel(common.TransactionCase):
    def setUp(self):
        super(TestHotel, self).setUp()

        self.hotel_folio_obj = self.env["hotel.folio"]
        self.hotel_folio_line = self.env["hotel.folio.line"]
        self.warehouse = self.env.ref("stock.warehouse0")
        self.partner = self.env.ref("base.res_partner_2")
        self.price_list = self.env.ref("product.list0")
        self.room = self.env.ref("hotel.hotel_room_0")
        cur_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

    def test_confirm_sale(self):
        self.hotel_folio.action_confirm()
        self.assertEqual(self.hotel_folio.state == "sale", True)

    def test_folio_cancel(self):
        self.hotel_folio.action_cancel()
        self.assertEqual(self.hotel_folio.state == "cancel", True)

    def test_folio_set_to_draft(self):
        self.hotel_folio.action_cancel_draft()
        self.assertEqual(self.hotel_folio.state == "draft", True)

    def test_set_done(self):
        self.hotel_folio.action_done()
        self.assertEqual(self.hotel_folio.state == "done", True)
