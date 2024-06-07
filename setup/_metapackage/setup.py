import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-calendar",
    description="Meta package for oca-calendar Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-calendar_export_ics>=15.0dev,<15.1dev',
        'odoo-addon-calendar_import_ics>=15.0dev,<15.1dev',
        'odoo-addon-resource_booking>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
