import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-calendar",
    description="Meta package for oca-calendar Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-resource_booking',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
