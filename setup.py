# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(name='office365-rest-client',
      version='3.2.2',
      description='Python api wrapper for Office365 API v3.2.2',
      author='SugarCRM',
      packages=find_packages(),
      install_requires=[
          'oauth2client>=4.0.0'
      ],
      zip_safe=False)
