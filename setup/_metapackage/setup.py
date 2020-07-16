import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-vertical-hotel",
    description="Meta package for oca-vertical-hotel Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-board_frontdesk',
        'odoo11-addon-hotel',
        'odoo11-addon-hotel_housekeeping',
        'odoo11-addon-hotel_housekeeping_planning',
        'odoo11-addon-hotel_reservation',
        'odoo11-addon-hotel_restaurant',
        'odoo11-addon-report_hotel_reservation',
        'odoo11-addon-report_hotel_restaurant',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
