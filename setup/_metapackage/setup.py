import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-vertical-hotel",
    description="Meta package for oca-vertical-hotel Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-hotel',
        'odoo14-addon-hotel_housekeeping',
        'odoo14-addon-hotel_reservation',
        'odoo14-addon-hotel_restaurant',
        'odoo14-addon-report_hotel_reservation',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
