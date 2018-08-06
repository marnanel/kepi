import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

setup(
        name='django-kepi',
        version='0.1.0',
        packages=['django-kepi'],
        description='ActivityPub for Django',
        long_description=README,
        author='Marnanel Thurman',
        author_email='marnanel@thurman.org.uk',
        url='https://gitlab.com/marnanel/django-kepi',
        license='GPL 2.0',
        install_requires=[
            'Django>=2.0',
            ]
        )
