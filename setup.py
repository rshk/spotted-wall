from setuptools import setup, find_packages

setup(
    name='spotted_wall',
    version='0.1',
    packages=find_packages(),
    url='https://github.com/rshk/spotted-wall',
    license='GPLv3+',
    author='Samuele Santi',
    author_email='samuele@samuelesanti.com',
    description='',
    install_requires=[
        'pygame',
        'zerorpc',
        'pyzmq<13',  # Version 13 is known not to work
        'flask',
    ],
    package_data={'': ['README.rst']},
)
