# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import config

from ..wizard.hotel_v19_import import XMLID_MODULE, import_from_v19


@tagged("post_install", "-at_install")
class TestImportV19(TransactionCase):
    """The 19.0 tables are the same as ours, so the committed data of this
    very database (demo rooms, services, ...) serves as the source."""

    def _import(self, dbname=None):
        return import_from_v19(
            self.env,
            dbname or self.env.cr.dbname,
            config["db_host"],
            config["db_port"],
            config["db_user"],
            config["db_password"],
        )

    def _imported(self, model):
        return self.env["ir.model.data"].search_count(
            [("module", "=", XMLID_MODULE), ("model", "=", model)]
        )

    def test_import_and_rerun(self):
        rooms = self.env["hotel.room"].search([])
        if not rooms:
            # the import reads committed data through its own connection,
            # so records created by the test are invisible to it
            self.skipTest("needs rooms in the database (install with demo data)")
        services = self.env["hotel.services"].search([])
        log = self._import()
        self.assertIn("Source module: vertical_hotel", log[0])
        self.assertEqual(self._imported("hotel.room"), len(rooms))
        self.assertEqual(self._imported("hotel.services"), len(services))
        copies = self.env["hotel.room"].search([("id", "not in", rooms.ids)])
        self.assertEqual(sorted(copies.mapped("name")), sorted(rooms.mapped("name")))
        original = rooms.sorted("id")[0]
        copy = copies.filtered(lambda room: room.name == original.name)[:1]
        self.assertEqual(copy.room_categ_id.name, original.room_categ_id.name)
        self.assertEqual(copy.capacity, original.capacity)
        self.assertEqual(copy.list_price, original.list_price)
        self.assertEqual(copy.type, "service")
        # second run: everything is already there
        self.assertIn("nothing new", self._import()[-1])

    def test_wizard_bad_database(self):
        wizard = self.env["hotel.v19.import.wizard"].create(
            {
                "source_db": "no_such_hotel_db_19",
                "source_host": config["db_host"],
                "source_port": config["db_port"],
            }
        )
        with self.assertRaises(UserError):
            wizard.action_import()
