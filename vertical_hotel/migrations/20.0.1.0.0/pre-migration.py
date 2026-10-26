# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)

OLD = "hotel"
NEW = "vertical_hotel"
OLD_REPORT_MODEL = "report.hotel.report_hotel_folio"
NEW_REPORT_MODEL = "report.vertical_hotel.report_hotel_folio"


def _rename_view_keys(cr):
    """QWeb views store their xmlid in ``key``; Odoo resolves t-call by it."""
    cr.execute(
        """
        UPDATE ir_ui_view v
           SET key = %s || substr(v.key, length(%s) + 1)
          FROM ir_model_data d
         WHERE d.model = 'ir.ui.view'
           AND d.res_id = v.id
           AND d.module = %s
           AND v.key LIKE %s
        """,
        (NEW + ".", OLD + ".", NEW, OLD + ".%"),
    )
    _logger.info("Renamed %s view keys from %s.* to %s.*", cr.rowcount, OLD, NEW)


def _rename_report_actions(cr):
    cr.execute(
        """
        UPDATE ir_act_report_xml
           SET report_name = %s || substr(report_name, length(%s) + 1)
         WHERE report_name LIKE %s
        """,
        (NEW + ".", OLD + ".", OLD + ".%"),
    )
    if column_exists(cr, "ir_act_report_xml", "report_file"):  # dropped in 20.0
        cr.execute(
            """
            UPDATE ir_act_report_xml
               SET report_file = %s || substr(report_file, length(%s) + 1)
             WHERE report_file LIKE %s
            """,
            (NEW + ".", OLD + ".", OLD + ".%"),
        )


def _rename_report_model(cr):
    """The folio report AbstractModel is named after the module
    (report.<module>.<template>): rename it in place instead of letting
    Odoo drop and recreate its ir.model / ir.model.fields records."""
    cr.execute("SELECT 1 FROM ir_model WHERE model = %s", (NEW_REPORT_MODEL,))
    if cr.fetchone():
        return
    old_xmlid = "model_" + OLD_REPORT_MODEL.replace(".", "_")
    new_xmlid = "model_" + NEW_REPORT_MODEL.replace(".", "_")
    cr.execute(
        "UPDATE ir_model SET model = %s WHERE model = %s",
        (NEW_REPORT_MODEL, OLD_REPORT_MODEL),
    )
    if not cr.rowcount:
        return
    cr.execute(
        "UPDATE ir_model_fields SET model = %s WHERE model = %s",
        (NEW_REPORT_MODEL, OLD_REPORT_MODEL),
    )
    cr.execute(
        "UPDATE ir_model_fields SET relation = %s WHERE relation = %s",
        (NEW_REPORT_MODEL, OLD_REPORT_MODEL),
    )
    cr.execute(
        """
        UPDATE ir_model_data
           SET name = %s
         WHERE module = %s AND model = 'ir.model' AND name = %s
        """,
        (new_xmlid, NEW, old_xmlid),
    )
    # field_<model>__<field>
    cr.execute(
        """
        UPDATE ir_model_data
           SET name = %s || substr(name, length(%s) + 1)
         WHERE module = %s AND model = 'ir.model.fields' AND name LIKE %s
        """,
        (
            "field_" + NEW_REPORT_MODEL.replace(".", "_") + "__",
            "field_" + OLD_REPORT_MODEL.replace(".", "_") + "__",
            NEW,
            "field_" + OLD_REPORT_MODEL.replace(".", "_") + "\\_\\_%",
        ),
    )
    _logger.info("Renamed model %s to %s", OLD_REPORT_MODEL, NEW_REPORT_MODEL)


def _rooms_and_services_as_service_products(cr):
    """Folios are now confirmed through sale.order.action_confirm(): room
    nights and hotel services must be service products, or sale_stock would
    create delivery orders for them. Products that already have stock moves
    are left alone."""
    cr.execute(
        """
        UPDATE product_template t
           SET type = 'service'
          FROM product_product p
         WHERE p.product_tmpl_id = t.id
           AND (p.isroom OR p.isservice
                OR p.id IN (SELECT product_id FROM hotel_room)
                OR p.id IN (SELECT product_id FROM hotel_services))
           AND t.type = 'consu'
           AND NOT t.is_storable
           AND NOT EXISTS (
                SELECT 1
                  FROM stock_move m
                  JOIN product_product pp ON pp.id = m.product_id
                 WHERE pp.product_tmpl_id = t.id
           )
        """
    )
    _logger.info("Set %s room/service products to type 'service'", cr.rowcount)


def migrate(cr, version):
    """Migrate from 19.0.

    Finish the rename of module ``hotel`` to ``vertical_hotel``: the module
    itself is renamed in the database beforehand, either by
    ``vertical_hotel/scripts/rename_hotel_to_vertical_hotel.py`` or by
    OpenUpgrade (``renamed_modules``). This handles what depends on the
    module name besides the XML-ID namespace. Every step is idempotent.
    """
    if not version:
        return
    cr.execute(
        "SELECT state FROM ir_module_module WHERE name = %s",
        (OLD,),
    )
    row = cr.fetchone()
    if row and row[0] in ("installed", "to upgrade", "to remove"):
        _logger.warning(
            "Module %r is still registered as %s next to %r. Run "
            "vertical_hotel/scripts/rename_hotel_to_vertical_hotel.py on a "
            "backup of the database before upgrading.",
            OLD,
            row[0],
            NEW,
        )
    _rename_view_keys(cr)
    _rename_report_actions(cr)
    _rename_report_model(cr)
    _rooms_and_services_as_service_products(cr)
