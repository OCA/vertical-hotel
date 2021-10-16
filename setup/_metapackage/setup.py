import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-vertical-hotel",
    description="Meta package for oca-vertical-hotel Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-board_frontdesk',
        'odoo10-addon-hotel',
        'odoo10-addon-hotel_housekeeping',
        'odoo10-addon-hotel_reservation',
        'odoo10-addon-hotel_restaurant',
        'odoo10-addon-report_hotel_reservation',
        'odoo10-addon-report_hotel_restaurant',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 10.0',
    ]
)
