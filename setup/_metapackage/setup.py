import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-vertical-hotel",
    description="Meta package for oca-vertical-hotel Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-hotel',
        'odoo12-addon-hotel_housekeeping',
        'odoo12-addon-hotel_reservation',
        'odoo12-addon-hotel_restaurant',
        'odoo12-addon-report_hotel_reservation',
        'odoo12-addon-report_hotel_restaurant',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
