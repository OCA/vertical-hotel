# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

OLD_MODULE = "hotel"


def pre_init_hook(env):
    """Refuse to install next to the module under its old name.

    ``hotel`` was renamed to ``vertical_hotel`` and both define the same
    models: installing ``vertical_hotel`` while ``hotel`` is still installed
    would leave two modules owning the same tables. Such a database must be
    renamed first (``scripts/rename_hotel_to_vertical_hotel.py`` or
    OpenUpgrade); after that ``hotel`` is gone and ``vertical_hotel`` is
    upgraded, not installed, so this hook does not run.
    """
    env.cr.execute(
        "SELECT state FROM ir_module_module WHERE name = %s",
        (OLD_MODULE,),
    )
    row = env.cr.fetchone()
    if row and row[0] in ("installed", "to install", "to upgrade", "to remove"):
        raise UserError(
            env._(
                "The module %(old)r is %(state)s in this database. It was "
                "renamed to %(new)r: do not install %(new)r next to it. Stop "
                "Odoo, make a backup and run "
                "vertical_hotel/scripts/rename_hotel_to_vertical_hotel.py on "
                "the database, then update %(new)r instead (see the module's "
                "changelog, 19.0.1.1.0).",
                old=OLD_MODULE,
                state=row[0],
                new="vertical_hotel",
            )
        )
