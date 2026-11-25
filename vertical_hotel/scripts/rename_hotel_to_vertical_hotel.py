# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Rename the installed module ``hotel`` to ``vertical_hotel`` in a database.

Odoo has no notion of a renamed module: with the new code in place it sees
``hotel`` as installed-but-missing and ``vertical_hotel`` as a new module.
Installing the latter would duplicate menus, groups, sequences, etc., and
uninstalling ``hotel`` would drop all hotel data. This script moves the
module record and all its XML-IDs to the new name so the regular upgrade
(``-u vertical_hotel``) keeps every existing record.

Run it on a backup, with Odoo stopped, before the first start on the new code:

    python3 rename_hotel_to_vertical_hotel.py -d <db> [--dry-run]
    odoo-bin -d <db> -u vertical_hotel --stop-after-init

Or from ``odoo-bin shell -d <db>`` (then exit and run the upgrade)::

    from odoo.addons.vertical_hotel.scripts.rename_hotel_to_vertical_hotel \
        import rename_module
    rename_module(env.cr); env.cr.commit()

The script is idempotent: running it on an already renamed database does
nothing.
"""

import argparse
import getpass
import logging
import sys

_logger = logging.getLogger("rename_hotel_to_vertical_hotel")

OLD = "hotel"
NEW = "vertical_hotel"
ACTIVE_STATES = ("installed", "to upgrade", "to remove", "to install")


def _module(cr, name):
    cr.execute("SELECT id, state FROM ir_module_module WHERE name = %s", (name,))
    return cr.fetchone()


def _table_exists(cr, table):
    cr.execute("SELECT 1 FROM pg_class WHERE relname = %s AND relkind = 'r'", (table,))
    return bool(cr.fetchone())


def _drop_placeholder(cr, module_id):
    """Remove the 'uninstalled' vertical_hotel row created by an Apps list
    update after the new code was deployed but before this script ran."""
    cr.execute(
        "SELECT count(*) FROM ir_model_data "
        "WHERE module = %s AND model != 'ir.module.module'",
        (NEW,),
    )
    if cr.fetchone()[0]:
        raise RuntimeError(
            f"{NEW!r} is uninstalled but already owns XML-IDs; refusing to merge."
        )
    cr.execute(
        "DELETE FROM ir_module_module_dependency WHERE module_id = %s", (module_id,)
    )
    if _table_exists(cr, "ir_module_module_exclusion"):
        cr.execute(
            "DELETE FROM ir_module_module_exclusion WHERE module_id = %s", (module_id,)
        )
    cr.execute(
        "DELETE FROM ir_model_data "
        "WHERE module = 'base' AND model = 'ir.module.module' AND name = %s",
        ("module_" + NEW,),
    )
    cr.execute("DELETE FROM ir_module_module WHERE id = %s", (module_id,))
    _logger.info("Removed placeholder record of uninstalled module %r", NEW)


def rename_module(cr):
    """Rename module ``hotel`` to ``vertical_hotel``. Returns True if renamed."""
    old, new = _module(cr, OLD), _module(cr, NEW)
    if not old:
        _logger.info("Module %r not found: nothing to do.", OLD)
        return False
    if old[1] not in ACTIVE_STATES:
        _logger.info("Module %r is %s: nothing to rename.", OLD, old[1])
        return False
    if new:
        if new[1] in ACTIVE_STATES:
            raise RuntimeError(
                f"Both {OLD!r} ({old[1]}) and {NEW!r} ({new[1]}) are installed; "
                "this needs a manual merge."
            )
        _drop_placeholder(cr, new[0])

    queries = [
        (
            "ir_module_module",
            "UPDATE ir_module_module SET name = %s WHERE name = %s",
            (NEW, OLD),
        ),
        (
            "module xmlid",
            (
                "UPDATE ir_model_data SET name = %s "
                "WHERE module = 'base' AND model = 'ir.module.module' AND name = %s"
            ),
            ("module_" + NEW, "module_" + OLD),
        ),
        (
            "ir_model_data",
            "UPDATE ir_model_data SET module = %s WHERE module = %s",
            (NEW, OLD),
        ),
        (
            "dependencies",
            "UPDATE ir_module_module_dependency SET name = %s WHERE name = %s",
            (NEW, OLD),
        ),
        (
            "view keys",
            (
                "UPDATE ir_ui_view SET key = %s || substr(key, length(%s) + 1) "
                "WHERE key LIKE %s"
            ),
            (NEW + ".", OLD + ".", OLD + ".%"),
        ),
    ]
    if _table_exists(cr, "ir_module_module_exclusion"):
        queries.append(
            (
                "exclusions",
                "UPDATE ir_module_module_exclusion SET name = %s WHERE name = %s",
                (NEW, OLD),
            )
        )
    if _table_exists(cr, "ir_translation"):  # Odoo < 16
        queries.append(
            (
                "translations",
                "UPDATE ir_translation SET module = %s WHERE module = %s",
                (NEW, OLD),
            )
        )
    for label, query, params in queries:
        cr.execute(query, params)
        _logger.info("%-16s %6d row(s)", label, cr.rowcount)
    _logger.info(
        "Module %r renamed to %r. Now run: odoo-bin -d <db> -u %s --stop-after-init",
        OLD,
        NEW,
        NEW,
    )
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("-d", "--database", required=True)
    parser.add_argument("--db_host", default=None)
    parser.add_argument("--db_port", default=None)
    parser.add_argument("-r", "--db_user", default=None)
    parser.add_argument(
        "-w",
        "--db_password",
        nargs="?",
        const="",
        default=None,
        help="give without a value to be prompted",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show what would change, then roll back"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    import psycopg2  # pylint: disable=import-outside-toplevel

    password = args.db_password
    if password == "":
        password = getpass.getpass("Database password: ")
    conn = psycopg2.connect(
        dbname=args.database,
        host=args.db_host,
        port=args.db_port,
        user=args.db_user,
        password=password,
    )
    try:
        with conn.cursor() as cr:
            rename_module(cr)
        if args.dry_run:
            conn.rollback()
            _logger.info("Dry run: changes rolled back.")
        else:
            conn.commit()
    except Exception:
        conn.rollback()
        _logger.exception("Rename failed, database left unchanged.")
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
