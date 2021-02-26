import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-calendar",
    description="Meta package for oca-calendar Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-calendar_partner_color',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
