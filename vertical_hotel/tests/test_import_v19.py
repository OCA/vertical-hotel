# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unittest
from contextlib import closing

import psycopg2
from psycopg2 import sql

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import config, file_open

from ..wizard.hotel_v19_import import XMLID_MODULE, import_from_v19

FIXTURE = "vertical_hotel/tests/data/hotel_v19_source.sql"


def _connect(dbname):
    return psycopg2.connect(
        dbname=dbname,
        host=config["db_host"] or None,
        port=config["db_port"] or None,
        user=config["db_user"] or None,
        password=config["db_password"] or None,
    )


@tagged("post_install", "-at_install")
class TestImportV19(TransactionCase):
    """Import from a real Odoo 19.0 database.

    The fixture holds the tables of an Odoo 19.0 database with the OCA hotel
    module as 19.0 creates them; it is loaded into a database of its own,
    which the import reads through its own connection, as it would read a
    customer's database."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source_db = f"{cls.env.cr.dbname}_hotel_v19"[:63]
        try:
            admin = _connect("postgres")
        except psycopg2.Error as error:
            raise unittest.SkipTest(
                f"no PostgreSQL maintenance access: {error}"
            ) from None
        admin.autocommit = True
        name = sql.Identifier(cls.source_db)
        with admin.cursor() as cr:
            cr.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(name))
            try:
                cr.execute(
                    sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(name)
                )
            except psycopg2.errors.InsufficientPrivilege as error:
                admin.close()
                raise unittest.SkipTest(f"cannot create a database: {error}") from None

        def drop():
            with admin.cursor() as cr:
                cr.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(name)
                )
            admin.close()

        cls.addClassCleanup(drop)
        with closing(_connect(cls.source_db)) as conn, file_open(FIXTURE) as fixture:
            with conn.cursor() as cr:
                cr.execute(fixture.read())
            conn.commit()
        # the 12% sales tax of the 19.0 rooms and breakfast, matched by amount
        cls.vat = cls.env["account.tax"].create(
            {
                "name": "Fixture VAT 12%",
                "amount": 12.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )

    def _import(self):
        return import_from_v19(self.env, self.source_db)

    def _imported(self, model):
        data = self.env["ir.model.data"].search(
            [("module", "=", XMLID_MODULE), ("model", "=", model)]
        )
        return self.env[model].browse(data.mapped("res_id"))

    def test_import_from_19(self):
        log = self._import()
        self.assertEqual(log[0], "Source module: hotel 19.0.1.0.0")

        rooms = self._imported("hotel.room").sorted("name")
        self.assertEqual(rooms.mapped("name"), ["FX-101", "FX-102"])
        self.assertEqual(rooms.mapped("list_price"), [100.0, 140.0])
        self.assertEqual(rooms.room_categ_id.name, "Fixture Suite")
        self.assertEqual(rooms.floor_id.name, "Fixture First Floor")
        self.assertEqual(rooms.room_amenities_ids.name, "Fixture Minibar")
        self.assertEqual(rooms.taxes_id, self.vat)
        self.assertEqual(
            (rooms[0].capacity, rooms[0].max_adult, rooms[0].max_child), (2, 2, 1)
        )
        service = self._imported("hotel.services")
        self.assertEqual(service.name, "Fixture Breakfast")
        self.assertEqual(service.service_categ_id.name, "Fixture Dining")

        folios = self._imported("hotel.folio").sorted("name")
        self.assertEqual(folios.mapped("name"), ["Folio/00002", "Folio/00003"])
        invoiced, open_folio = folios
        self.assertEqual(invoiced.order_id.name, "S00002")
        self.assertEqual(
            invoiced.partner_id.email, "invoiced.guest@example.com", "customer copied"
        )
        self.assertEqual(invoiced.room_line_ids.product_id, rooms[0].product_id)
        self.assertEqual(invoiced.service_line_ids.product_id, service.product_id)
        self.assertEqual(invoiced.room_line_ids.tax_ids, self.vat)
        self.assertEqual(
            self.env["folio.room.line"]
            .search([("folio_id", "=", invoiced.id)])
            .room_id,
            rooms[0],
        )
        self.assertEqual(
            (invoiced.state, open_folio.state), ("sale", "sale"), "confirmed in 19.0"
        )
        # invoiced in 19.0, where the invoice stays: not to invoice again
        self.assertTrue(invoiced.order_id.invoicing_closed)
        self.assertEqual(invoiced.invoice_status, "invoiced")
        self.assertIn("INV/2026/00001", invoiced.order_id.message_ids[:1].body)
        # not invoiced in 19.0: still to invoice here
        self.assertFalse(open_folio.order_id.invoicing_closed)
        self.assertEqual(open_folio.invoice_status, "to invoice")

        # second run: everything is already there
        self.assertIn("nothing new", self._import()[-1])

    def test_wizard_bad_database(self):
        wizard = self.env["hotel.v19.import.wizard"].create(
            {"source_db": "no_such_hotel_db_19"}
        )
        with self.assertRaises(UserError):
            wizard.action_import()
