from odoo.upgrade import openupgrade


@openupgrade.migrate()
def migrate(cr, version):

    """
    Rename activity_id to parent_id in hotel_housekeeping_activity_type
    """

    table_name = "hotel_housekeeping_activity_type"

    if openupgrade.table_exists(cr, table_name):

        openupgrade.rename_columns(
            cr,
            {
                table_name: [
                    ("activity_id", "parent_id"),
                ],
            },
        )