from setuptools import setup, find_packages

setup(
    name='spotted_wall',
    version=__import__('spotted_wall').__version__,
    description='A display with scrolling messages on it, pygame-powered',
    packages=find_packages(),
    url='https://github.com/rshk/spotted-wall',
    license='Apache License, Version 2.0',
    author='Samuele ~redShadow~ Santi',
    author_email='redshadow@hackzine.org',
    install_requires=[
        'pygame',
        'smartrpyc',
    ],
    package_data={'': ['README.rst']},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
    ],
)
