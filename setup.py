from setuptools import setup

setup(
    name='chromarestserver',
    packages=['chromarestserver'],
    include_package_data=True,
    install_requires=[
        'falcon',
        'future',
        'hidapi',
        'jsonschema',
        'tinydb',
    ],
)
