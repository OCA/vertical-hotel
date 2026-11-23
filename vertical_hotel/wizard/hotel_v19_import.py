# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Copy the hotel data of an Odoo 19.0 database into this (20.0) database.

The 19.0 database is opened read-only with psycopg2 and is never changed; the
module there may be called ``hotel`` or ``vertical_hotel``. Every imported
record gets an XML-ID ``__hotel_v19__.<source uuid>_<table>_<id>``, so running
the import again only adds what is missing.

Copied: company extra-hours setting, floors, room / amenity / service types,
amenities, services, rooms (with images, taxes, amenities, status), the
customers and salespersons used on folios, folios with their room lines,
service lines, other order lines and room occupancy. Invoices and payments are
not copied (accounting history cannot be re-created by copying); the source
invoice numbers are noted on each order.
"""

import logging
import os
from typing import ClassVar

import psycopg2

from odoo import Command, fields, models
from odoo.exceptions import UserError
from odoo.tools import BinaryBytes, config

_logger = logging.getLogger(__name__)

XMLID_MODULE = "__hotel_v19__"
CONFIG_PREFIX = "vertical_hotel_import_"


class HotelV19Importer:
    """Import from an open (read-only) psycopg2 connection to a 19.0 db."""

    def __init__(self, env, conn, filestore=None):
        self.env = env(
            context=dict(
                env.context,
                hotel_v19_import=True,
                tracking_disable=True,
                mail_create_nolog=True,
                mail_notrack=True,
                active_test=False,
            )
        )
        self.src = conn.cursor()
        self.filestore = filestore
        self.company = self.env.company
        self.log = []
        self.stats = {}
        self.src.execute(
            "SELECT value FROM ir_config_parameter WHERE key = 'database.uuid'"
        )
        self.prefix = (self.src.fetchone() or ["nouuid"])[0].replace("-", "")[:8]
        self.langs = [
            code for code, __ in self.env["res.lang"].get_installed() if code != "en_US"
        ]

    # helpers --------------------------------------------------------------

    def _rows(self, query, params=None):
        self.src.execute(query, params or ())
        names = [col.name for col in self.src.description]
        return [dict(zip(names, row, strict=True)) for row in self.src.fetchall()]

    def _has_column(self, table, column):
        self.src.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s",
            (table, column),
        )
        return bool(self.src.fetchone())

    def _xmlid(self, table, src_id):
        return f"{self.prefix}_{table}_{src_id}"

    def _mapped(self, model, table, src_id):
        if not src_id:
            return self.env[model]
        data = self.env["ir.model.data"].search(
            [
                ("module", "=", XMLID_MODULE),
                ("name", "=", self._xmlid(table, src_id)),
                ("model", "=", model),
            ],
            limit=1,
        )
        return self.env[model].browse(data.res_id).exists()

    def _remember(self, record, table, src_id):
        self.env["ir.model.data"].create(
            {
                "module": XMLID_MODULE,
                "name": self._xmlid(table, src_id),
                "model": record._name,
                "res_id": record.id,
                "noupdate": True,
            }
        )
        self.stats[table] = self.stats.get(table, 0) + 1

    @staticmethod
    def _text(value):
        """jsonb translations -> en_US (or first) value; plain values as-is."""
        if isinstance(value, dict):
            return value.get("en_US") or next(iter(value.values()), "") or ""
        return value

    def _translate(self, record, field, value):
        if not isinstance(value, dict):
            return
        for lang in self.langs:
            if value.get(lang) and value.get(lang) != value.get("en_US"):
                record.with_context(lang=lang)[field] = value[lang]

    def _note(self, message):
        _logger.info("v19 import: %s", message)
        self.log.append(message)

    # reference data (matched, never created) ------------------------------

    def _load_reference_maps(self):
        env = self.env
        users = {u.login: u for u in env["res.users"].search([])}
        self.user_map = {
            row["id"]: users.get(row["login"])
            for row in self._rows("SELECT id, login FROM res_users")
        }
        countries = {c.code: c for c in env["res.country"].search([])}
        self.country_map = {
            row["id"]: countries.get(row["code"])
            for row in self._rows("SELECT id, code FROM res_country")
        }
        states = {
            (s.country_id.code, s.code): s for s in env["res.country.state"].search([])
        }
        self.state_map = {
            row["id"]: states.get((row["country"], row["code"]))
            for row in self._rows(
                "SELECT s.id, s.code, c.code AS country FROM res_country_state s "
                "JOIN res_country c ON c.id = s.country_id"
            )
        }
        uoms = {
            u.with_context(lang="en_US").name.lower(): u
            for u in env["uom.uom"].search([])
        }
        self.uom_map = {
            row["id"]: uoms.get((self._text(row["name"]) or "").lower())
            for row in self._rows("SELECT id, name FROM uom_uom")
        }
        self.default_uom = env.ref("uom.product_uom_unit")
        taxes = env["account.tax"].search([("company_id", "=", self.company.id)])
        self.tax_map = {}
        for row in self._rows(
            "SELECT id, name, amount, amount_type, type_tax_use FROM account_tax"
        ):
            candidates = taxes.filtered(
                lambda t, row=row: (
                    t.type_tax_use == row["type_tax_use"]
                    and t.amount_type == row["amount_type"]
                    and abs(t.amount - float(row["amount"])) < 0.0001
                )
            )
            by_name = candidates.filtered(
                lambda t, row=row: (
                    t.with_context(lang="en_US").name == self._text(row["name"])
                )
            )
            self.tax_map[row["id"]] = (by_name or candidates)[:1]
        pricelists = env["product.pricelist"].search(
            [("company_id", "in", [self.company.id, False])]
        )
        self.pricelist_map = {}
        for row in self._rows(
            "SELECT p.id, p.name, c.name AS currency FROM product_pricelist p "
            "JOIN res_currency c ON c.id = p.currency_id"
        ):
            same_currency = pricelists.filtered(
                lambda p, row=row: p.currency_id.name == row["currency"]
            )
            by_name = same_currency.filtered(
                lambda p, row=row: (
                    p.with_context(lang="en_US").name == self._text(row["name"])
                )
            )
            self.pricelist_map[row["id"]] = (by_name or same_currency or pricelists)[:1]
        warehouses = env["stock.warehouse"].search(
            [("company_id", "=", self.company.id)]
        )
        self.warehouse_map = {
            row["id"]: warehouses.filtered(lambda w, row=row: w.code == row["code"])[:1]
            or warehouses[:1]
            for row in self._rows("SELECT id, code FROM stock_warehouse")
        }

    # (relation table, column of the record, column of the tax)
    TAX_RELATIONS: ClassVar[dict] = {
        "product": ("product_taxes_rel", "prod_id", "tax_id"),
        "product_supplier": ("product_supplier_taxes_rel", "prod_id", "tax_id"),
        "order_line": (
            "account_tax_sale_order_line_rel",
            "sale_order_line_id",
            "account_tax_id",
        ),
    }

    def _taxes(self, relation, src_id):
        table, key, tax_column = self.TAX_RELATIONS[relation]
        rows = self._rows(
            f"SELECT {tax_column} AS tax FROM {table} WHERE {key} = %s",
            (src_id,),
        )
        return self.env["account.tax"].union(
            self.tax_map[row["tax"]] for row in rows if self.tax_map.get(row["tax"])
        )

    # partners -------------------------------------------------------------

    def _partner(self, src_id):
        if not src_id:
            return self.env["res.partner"]
        partner = self._mapped("res.partner", "res_partner", src_id)
        if partner:
            return partner
        rows = self._rows("SELECT * FROM res_partner WHERE id = %s", (src_id,))
        if not rows:
            return self.env["res.partner"]
        row = rows[0]
        # a user's own contact: reuse the partner of the same user here
        user = self.user_map.get(self.user_partner_ids.get(row["id"]))
        if user:
            self._remember(user.partner_id, "res_partner", src_id)
            return user.partner_id
        parent = self._partner(row.get("parent_id"))
        if row.get("email"):
            existing = self.env["res.partner"].search(
                [("email", "=ilike", row["email"]), ("name", "=", row["name"])], limit=1
            )
            if existing:
                self._remember(existing, "res_partner", src_id)
                return existing
        vals = {
            "name": row["name"],
            "parent_id": parent.id,
            "type": row.get("type") or "contact",
            "is_company": row.get("is_company"),
            "email": row.get("email"),
            "phone": row.get("phone"),
            "street": row.get("street"),
            "street2": row.get("street2"),
            "city": row.get("city"),
            "zip": row.get("zip"),
            "country_id": self.country_map.get(row.get("country_id"), False)
            and self.country_map[row["country_id"]].id,
            "state_id": self.state_map.get(row.get("state_id"), False)
            and self.state_map[row["state_id"]].id,
            "vat": row.get("vat"),
            "ref": row.get("ref"),
            "comment": row.get("comment"),
            "active": row.get("active", True),
        }
        if row.get("lang") in self.langs + ["en_US"]:
            vals["lang"] = row["lang"]
        partner = self.env["res.partner"].create(vals)
        self._remember(partner, "res_partner", src_id)
        return partner

    # configuration --------------------------------------------------------

    def _import_company_settings(self):
        if self._has_column("res_company", "additional_hours"):
            rows = self._rows(
                "SELECT additional_hours FROM res_company ORDER BY id LIMIT 1"
            )
            if (
                rows
                and rows[0]["additional_hours"]
                and not self.company.additional_hours
            ):
                self.company.additional_hours = rows[0]["additional_hours"]

    def _import_floors(self):
        Floor = self.env["hotel.floor"]
        for row in self._rows("SELECT id, name, sequence FROM hotel_floor ORDER BY id"):
            if self._mapped("hotel.floor", "hotel_floor", row["id"]):
                continue
            floor = Floor.search([("name", "=", row["name"])], limit=1) or Floor.create(
                {"name": row["name"], "sequence": row["sequence"]}
            )
            self._remember(floor, "hotel_floor", row["id"])

    def _import_types(self, table, model, parent_column):
        """Category trees (room/amenity/service types), parents first."""
        rows = self._rows(
            f"SELECT t.id, t.{parent_column} AS parent, c.name "
            f"FROM {table} t JOIN product_category c ON c.id = t.product_categ_id "
            "ORDER BY t.id"
        )
        by_id = {row["id"]: row for row in rows}

        def ensure(row):
            record = self._mapped(model, table, row["id"])
            if record:
                return record
            parent = ensure(by_id[row["parent"]]) if row["parent"] in by_id else None
            name = self._text(row["name"])
            Model = self.env[model]
            record = Model.search(
                [
                    ("name", "=", name),
                    (parent_column, "=", parent.id if parent else False),
                ],
                limit=1,
            ) or Model.create(
                {"name": name, parent_column: parent.id if parent else False}
            )
            self._remember(record, table, row["id"])
            return record

        for row in rows:
            ensure(row)

    # products -------------------------------------------------------------

    def _product_vals(self, product_id):
        row = self._rows(
            "SELECT p.id, p.product_tmpl_id, p.default_code, p.barcode, p.isroom, "
            "p.iscategid, p.isservice, p.standard_price, t.name, t.list_price, "
            "t.type, t.uom_id, t.description, t.description_sale, t.sale_ok, "
            "t.purchase_ok, t.active, t.color, t.invoice_policy "
            "FROM product_product p "
            "JOIN product_template t ON t.id = p.product_tmpl_id "
            "WHERE p.id = %s",
            (product_id,),
        )[0]
        standard_price = row["standard_price"]
        if isinstance(standard_price, dict):
            standard_price = next(iter(standard_price.values()), 0.0)
        barcode = row["barcode"]
        if barcode and self.env["product.product"].search_count(
            [("barcode", "=", barcode)]
        ):
            self._note(
                f"Barcode {barcode} already used, not copied "
                f"({self._text(row['name'])})"
            )
            barcode = False
        vals = {
            "name": self._text(row["name"]),
            "list_price": float(row["list_price"] or 0.0),
            "standard_price": float(standard_price or 0.0),
            "default_code": row["default_code"],
            "barcode": barcode,
            "description": self._text(row["description"]),
            "description_sale": self._text(row["description_sale"]),
            "sale_ok": row["sale_ok"],
            "purchase_ok": row["purchase_ok"],
            "active": row["active"],
            "color": row["color"] or 0,
            "isroom": row["isroom"],
            "iscategid": row["iscategid"],
            "isservice": row["isservice"],
            "uom_id": (self.uom_map.get(row["uom_id"]) or self.default_uom).id,
            "taxes_id": [
                Command.set(self._taxes("product", row["product_tmpl_id"]).ids)
            ],
            "supplier_taxes_id": [
                Command.set(self._taxes("product_supplier", row["product_tmpl_id"]).ids)
            ],
        }
        if row["invoice_policy"]:
            vals["invoice_policy"] = row["invoice_policy"]
        if not (row["isroom"] or row["isservice"]):
            vals["type"] = row["type"]
        image = self._image(row["product_tmpl_id"])
        if image:
            vals["image_1920"] = image
        return vals, row

    def _image(self, template_id):
        if not self.filestore:
            return None
        rows = self._rows(
            "SELECT store_fname, name FROM ir_attachment WHERE res_model = "
            "'product.template' AND res_field = 'image_1920' AND res_id = %s",
            (template_id,),
        )
        if not rows or not rows[0]["store_fname"]:
            return None
        path = os.path.join(self.filestore, rows[0]["store_fname"])
        if not os.path.isfile(path):
            self._note(f"Image file missing in filestore: {path}")
            return None
        with open(path, "rb") as image_file:
            return BinaryBytes(image_file.read(), filename=rows[0]["name"] or "image")

    def _finish_product(self, record, row):
        self._translate(record, "name", row["name"])

    def _import_amenities(self):
        for row in self._rows(
            "SELECT id, product_id, amenities_categ_id, product_manager "
            "FROM hotel_room_amenities ORDER BY id"
        ):
            if self._mapped("hotel.room.amenities", "hotel_room_amenities", row["id"]):
                continue
            vals, product_row = self._product_vals(row["product_id"])
            vals.update(
                amenities_categ_id=self._mapped(
                    "hotel.room.amenities.type",
                    "hotel_room_amenities_type",
                    row["amenities_categ_id"],
                ).id,
                product_manager=(
                    self.user_map.get(row["product_manager"]) or self.env["res.users"]
                ).id,
            )
            amenity = self.env["hotel.room.amenities"].create(vals)
            self._finish_product(amenity.product_id, product_row)
            self._remember(amenity, "hotel_room_amenities", row["id"])
            self._remember(amenity.product_id, "product_product", row["product_id"])

    def _import_services(self):
        for row in self._rows(
            "SELECT id, product_id, service_categ_id, product_manager "
            "FROM hotel_services ORDER BY id"
        ):
            if self._mapped("hotel.services", "hotel_services", row["id"]):
                continue
            vals, product_row = self._product_vals(row["product_id"])
            vals.update(
                service_categ_id=self._mapped(
                    "hotel.service.type", "hotel_service_type", row["service_categ_id"]
                ).id,
                product_manager=(
                    self.user_map.get(row["product_manager"]) or self.env["res.users"]
                ).id,
            )
            service = self.env["hotel.services"].create(vals)
            self._finish_product(service.product_id, product_row)
            self._remember(service, "hotel_services", row["id"])
            self._remember(service.product_id, "product_product", row["product_id"])

    def _import_rooms(self):
        for row in self._rows(
            "SELECT id, product_id, floor_id, max_adult, max_child, room_categ_id, "
            "capacity, product_manager, status FROM hotel_room ORDER BY id"
        ):
            if self._mapped("hotel.room", "hotel_room", row["id"]):
                continue
            vals, product_row = self._product_vals(row["product_id"])
            amenity_ids = [
                self._mapped(
                    "hotel.room.amenities", "hotel_room_amenities", a["amenity"]
                ).id
                for a in self._rows(
                    "SELECT hotel_room_amenities_id AS amenity FROM "
                    "hotel_room_hotel_room_amenities_rel WHERE hotel_room_id = %s",
                    (row["id"],),
                )
            ]
            vals.update(
                floor_id=self._mapped("hotel.floor", "hotel_floor", row["floor_id"]).id,
                max_adult=row["max_adult"],
                max_child=row["max_child"],
                room_categ_id=self._mapped(
                    "hotel.room.type", "hotel_room_type", row["room_categ_id"]
                ).id,
                capacity=row["capacity"] or 1,
                product_manager=(
                    self.user_map.get(row["product_manager"]) or self.env["res.users"]
                ).id,
                room_amenities_ids=[Command.set([a for a in amenity_ids if a])],
            )
            room = self.env["hotel.room"].create(vals)
            self._finish_product(room.product_id, product_row)
            self._remember(room, "hotel_room", row["id"])
            self._remember(room.product_id, "product_product", row["product_id"])
            self.room_status[room.id] = (row["status"], product_row["isroom"])

    def _product(self, src_id):
        """Any other product used on an order line."""
        if not src_id:
            return self.env["product.product"]
        product = self._mapped("product.product", "product_product", src_id)
        if product:
            return product
        vals, product_row = self._product_vals(src_id)
        existing = self.env["product.product"]
        if vals.get("default_code"):
            existing = existing.search(
                [("default_code", "=", vals["default_code"])], limit=1
            )
        product = existing or self.env["product.product"].create(vals)
        if not existing:
            self._finish_product(product, product_row)
        self._remember(product, "product_product", src_id)
        return product

    # folios ---------------------------------------------------------------

    def _import_folios(self):
        folio_columns = (
            "f.id, f.name AS folio_name, f.checkin_date, f.checkout_date, "
            "f.hotel_policy, f.duration, f.hotel_invoice_id"
        )
        for extra in ("adults", "children", "total_guest"):
            if self._has_column("hotel_folio", extra):
                folio_columns += f", f.{extra}"
        rows = self._rows(
            f"SELECT {folio_columns}, o.id AS order_id, o.name AS order_name, "
            "o.partner_id, o.partner_invoice_id, o.partner_shipping_id, "
            "o.pricelist_id, o.warehouse_id, o.date_order, o.user_id, "
            "o.client_order_ref, o.origin, o.note, o.validity_date, o.state "
            "FROM hotel_folio f JOIN sale_order o ON o.id = f.order_id ORDER BY f.id"
        )
        for row in rows:
            if self._mapped("hotel.folio", "hotel_folio", row["id"]):
                continue
            try:
                with self.env.cr.savepoint():
                    self._import_folio(row)
            except Exception as error:  # noqa: BLE001 - reported, import continues
                self._note(f"Folio {row['folio_name']} NOT imported: {error}")
                self.stats["folio_errors"] = self.stats.get("folio_errors", 0) + 1

    def _import_folio(self, row):
        partner = self._partner(row["partner_id"])
        folio = self.env["hotel.folio"].create(
            {
                "name": row["folio_name"],
                "partner_id": partner.id,
                "partner_invoice_id": (
                    self._partner(row["partner_invoice_id"]) or partner
                ).id,
                "partner_shipping_id": (
                    self._partner(row["partner_shipping_id"]) or partner
                ).id,
                "pricelist_id": self.pricelist_map.get(
                    row["pricelist_id"], self.env["product.pricelist"]
                ).id,
                "warehouse_id": self.warehouse_map.get(
                    row["warehouse_id"], self.env["stock.warehouse"]
                ).id,
                "date_order": row["date_order"],
                "user_id": (self.user_map.get(row["user_id"]) or self.env.user).id,
                "client_order_ref": row["client_order_ref"],
                "origin": row["origin"],
                "note": row["note"],
                "validity_date": row["validity_date"],
                "checkin_date": row["checkin_date"],
                "checkout_date": row["checkout_date"],
                "hotel_policy": row["hotel_policy"] or "manual",
                "duration": row["duration"],
                "company_id": self.company.id,
            }
        )
        order = folio.order_id
        order.name = row["order_name"]
        done_lines = set()

        line_fields = (
            "l.id AS line_id, l.product_id, l.name, l.product_uom_qty, "
            "l.product_uom_id, "
            "l.price_unit, l.discount, l.sequence"
        )
        for line in self._rows(
            "SELECT h.id, h.checkin_date, h.checkout_date, h.is_reserved, "
            f"{line_fields} "
            "FROM hotel_folio_line h JOIN sale_order_line l ON l.id = h.order_line_id "
            "WHERE h.folio_id = %s ORDER BY l.sequence, l.id",
            (row["id"],),
        ):
            self.env["hotel.folio.line"].create(
                dict(
                    self._line_vals(line),
                    folio_id=folio.id,
                    checkin_date=line["checkin_date"],
                    checkout_date=line["checkout_date"],
                    is_reserved=line["is_reserved"],
                )
            )
            done_lines.add(line["line_id"])
        for line in self._rows(
            f"SELECT h.id, h.ser_checkin_date, h.ser_checkout_date, {line_fields} "
            "FROM hotel_service_line h "
            "JOIN sale_order_line l ON l.id = h.service_line_id "
            "WHERE h.folio_id = %s ORDER BY l.sequence, l.id",
            (row["id"],),
        ):
            self.env["hotel.service.line"].create(
                dict(
                    self._line_vals(line),
                    folio_id=folio.id,
                    ser_checkin_date=line["ser_checkin_date"],
                    ser_checkout_date=line["ser_checkout_date"],
                )
            )
            done_lines.add(line["line_id"])
        # sections, notes and products added on the order itself
        downpayment = (
            "AND NOT COALESCE(l.is_downpayment, false) "
            if self._has_column("sale_order_line", "is_downpayment")
            else ""
        )
        for line in self._rows(
            f"SELECT {line_fields}, l.display_type FROM sale_order_line l "
            f"WHERE l.order_id = %s {downpayment}ORDER BY l.sequence, l.id",
            (row["order_id"],),
        ):
            if line["line_id"] in done_lines:
                continue
            vals = self._line_vals(line)
            if line["display_type"]:
                vals = {
                    "display_type": line["display_type"],
                    "name": line["name"],
                    "sequence": line["sequence"],
                }
            self.env["sale.order.line"].create(dict(vals, order_id=order.id))

        # room occupancy exactly as in the source
        folio_room_lines = self.env["folio.room.line"].search(
            [("folio_id", "=", folio.id)]
        )
        folio_room_lines.unlink()
        for occupancy in self._rows(
            "SELECT room_id, check_in, check_out FROM folio_room_line "
            "WHERE folio_id = %s",
            (row["id"],),
        ):
            room = self._mapped("hotel.room", "hotel_room", occupancy["room_id"])
            if room:
                self.env["folio.room.line"].create(
                    {
                        "room_id": room.id,
                        "check_in": occupancy["check_in"],
                        "check_out": occupancy["check_out"],
                        "folio_id": folio.id,
                    }
                )

        order.write({"state": row["state"], "date_order": row["date_order"]})
        self._post_origin_note(order, row)
        self._remember(folio, "hotel_folio", row["id"])

    def _line_vals(self, line):
        product = self._product(line["product_id"])
        vals = {
            "product_id": product.id,
            "name": line["name"],
            "product_uom_qty": float(line["product_uom_qty"] or 0.0),
            "price_unit": float(line["price_unit"] or 0.0),
            "discount": float(line["discount"] or 0.0),
            "sequence": line["sequence"],
            "tax_ids": [Command.set(self._taxes("order_line", line["line_id"]).ids)],
        }
        uom = self.uom_map.get(line["product_uom_id"])
        if uom:
            vals["product_uom_id"] = uom.id
        return vals

    def _post_origin_note(self, order, row):
        details = [
            f"Imported from Odoo 19 (folio id {row['id']}, order {row['order_name']})."
        ]
        guests = [
            f"{label}: {row[key]}"
            for key, label in (
                ("adults", "Adults"),
                ("children", "Children"),
                ("total_guest", "Guests"),
            )
            if row.get(key)
        ]
        if guests:
            details.append(", ".join(guests))
        invoices = self._rows(
            "SELECT DISTINCT m.name, m.state FROM account_move m "
            "JOIN account_move_line ml ON ml.move_id = m.id "
            "JOIN sale_order_line_invoice_rel r ON r.invoice_line_id = ml.id "
            "JOIN sale_order_line sl ON sl.id = r.order_line_id "
            "WHERE sl.order_id = %s ORDER BY m.name",
            (row["order_id"],),
        )
        if invoices:
            details.append(
                "Invoices in Odoo 19 (not copied): "
                + ", ".join(f"{inv['name']} ({inv['state']})" for inv in invoices)
            )
        order.message_post(
            body="\n".join(details),
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )

    # main -----------------------------------------------------------------

    def run(self):
        self.src.execute(
            "SELECT name, latest_version FROM ir_module_module "
            "WHERE name IN ('hotel', 'vertical_hotel') AND state = 'installed'"
        )
        source_module = self.src.fetchone()
        if not source_module:
            raise UserError(
                self.env._("The source database has no installed hotel module.")
            )
        self._note(f"Source module: {source_module[0]} {source_module[1]}")
        self.room_status = {}
        self.user_partner_ids = {
            row["partner_id"]: row["id"]
            for row in self._rows("SELECT id, partner_id FROM res_users")
        }
        self._load_reference_maps()
        self._import_company_settings()
        self._import_floors()
        self._import_types("hotel_room_type", "hotel.room.type", "categ_id")
        self._import_types(
            "hotel_room_amenities_type", "hotel.room.amenities.type", "amenity_id"
        )
        self._import_types("hotel_service_type", "hotel.service.type", "service_id")
        self._import_amenities()
        self._import_services()
        self._import_rooms()
        self._import_folios()
        for room_id, (status, available) in self.room_status.items():
            self.env["hotel.room"].browse(room_id).write(
                {"status": status or "available", "isroom": available}
            )
        summary = ", ".join(
            f"{table}: {count}" for table, count in sorted(self.stats.items())
        )
        self._note(f"Created: {summary or 'nothing new'}")
        return self.log


def connect_source(dbname, host=None, port=None, user=None, password=None):
    """Read-only connection: the 19.0 database is never modified."""
    return psycopg2.connect(
        dbname=dbname,
        host=host or None,
        port=port or None,
        user=user or None,
        password=password or None,
        options="-c default_transaction_read_only=on",
    )


def import_from_v19(
    env, dbname, host=None, port=None, user=None, password=None, filestore=None
):
    if filestore is None:
        guess = os.path.join(config["data_dir"], "filestore", dbname)
        filestore = guess if os.path.isdir(guess) else None
    conn = connect_source(dbname, host, port, user, password)
    try:
        return HotelV19Importer(env, conn, filestore).run()
    finally:
        conn.close()


class HotelV19ImportWizard(models.TransientModel):
    _name = "hotel.v19.import.wizard"
    _description = "Import hotel data from an Odoo 19 database"

    source_db = fields.Char("Odoo 19 database", required=True)
    source_host = fields.Char("Host", help="Empty: local socket")
    source_port = fields.Integer("Port", default=5432)
    source_user = fields.Char("User")
    source_password = fields.Char("Password")
    source_filestore = fields.Char(
        "Filestore folder",
        help="Folder with the 19.0 database's files, for room/service images, "
        "e.g. ~/.local/share/Odoo/filestore/<database>. Empty: same data "
        "folder as this server, if it exists.",
    )
    result = fields.Text(readonly=True)

    def action_import(self):
        self.ensure_one()
        try:
            log = import_from_v19(
                self.env,
                self.source_db,
                self.source_host,
                self.source_port,
                self.source_user,
                self.source_password,
                os.path.expanduser(self.source_filestore)
                if self.source_filestore
                else None,
            )
        except psycopg2.OperationalError as error:
            raise UserError(
                self.env._("Cannot connect to the Odoo 19 database:\n%s", error)
            ) from error
        self.write({"result": "\n".join(log), "source_password": False})
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }


def post_init_hook(env):
    """Run the import at installation when the Odoo configuration file names
    the 19.0 database, e.g.::

        [options]
        vertical_hotel_import_db = customer-19
        vertical_hotel_import_port = 5432
    """
    dbname = config.get(CONFIG_PREFIX + "db")
    if not dbname:
        return
    _logger.info("Importing hotel data from Odoo 19 database %s", dbname)
    try:
        with env.cr.savepoint():
            log = import_from_v19(
                env,
                dbname,
                config.get(CONFIG_PREFIX + "host"),
                config.get(CONFIG_PREFIX + "port"),
                config.get(CONFIG_PREFIX + "user"),
                config.get(CONFIG_PREFIX + "password"),
                config.get(CONFIG_PREFIX + "filestore"),
            )
        _logger.info("Hotel import from %s done (%s steps logged)", dbname, len(log))
    except Exception:
        _logger.exception(
            "Hotel import from %s failed; the module is installed, run the import "
            "again from Hotel Management > Configuration > Import from Odoo 19.",
            dbname,
        )
