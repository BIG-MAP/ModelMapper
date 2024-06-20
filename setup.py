from setuptools import setup, find_packages

setup(
    name='BatteryModelMapper',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
        'rdflib',
        'jsonschema',
        'pybamm'
    ],
    entry_points={
        'console_scripts': [
            'BatteryModelMapper=BatteryModelMapper.__main__:main',
        ],
    },
)
