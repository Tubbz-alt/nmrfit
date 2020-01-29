from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

pkgs = find_packages(exclude=('examples', 'docs'))

setup(
    name='nmrfit',
    version='0.1.0',
    description='Quantitative NMR package.',
    long_description=readme,
    author='Sean M. Colby',
    author_email='sean.colby@pnnl.gov',
    url='https://github.com/pnnl/nmrfit',
    license=license,
    packages=pkgs,
    install_requires=required,
)
