import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-calendar",
    description="Meta package for oca-calendar Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-calendar_event_link_base',
        'odoo12-addon-calendar_event_link_project_task',
        'odoo12-addon-resource_booking',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 12.0',
    ]
)
