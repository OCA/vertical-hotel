# Copyright (C) 2024-TODAY Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.upgrade import openupgrade


@openupgrade.migrate()
def migrate(cr, version):
    """
    Rename activity_id to parent_id in hotel_housekeeping_activity_type
    """
    if openupgrade.table_exists(cr, "hotel_housekeeping_activity_type"):
        openupgrade.rename_columns(
            cr,
            {
                "hotel_housekeeping_activity_type": [
                    ("activity_id", "parent_id"),
                ],
            },
        )
