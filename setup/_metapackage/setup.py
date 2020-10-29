import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-vertical-hotel",
    description="Meta package for oca-vertical-hotel Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-hotel',
        'odoo13-addon-hotel_housekeeping',
        'odoo13-addon-hotel_reservation',
        'odoo13-addon-hotel_restaurant',
        'odoo13-addon-report_hotel_reservation',
        'odoo13-addon-report_hotel_restaurant',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
