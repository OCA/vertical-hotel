import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-vertical-hotel",
    description="Meta package for oca-vertical-hotel Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-hotel>=15.0dev,<15.1dev',
        'odoo-addon-hotel_housekeeping>=15.0dev,<15.1dev',
        'odoo-addon-hotel_restaurant>=15.0dev,<15.1dev',
        'odoo-addon-report_hotel_restaurant>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
