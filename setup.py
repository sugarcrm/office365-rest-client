# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

setup(name='office365-rest-client',
      version='3.3.5',
      description='Python api wrapper for Office365 API v3.3.5',
      author='SugarCRM',
      packages=find_packages(),
      install_requires=[
          'oauth2client>=4.0.0',
          'requests>=2.31.0',
      ],
      zip_safe=False)
