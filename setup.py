# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(name='office365-rest-client',
      version='0.0.1',
      description='Python api wrapper for Office365 API v1.0',
      url='https://bitbucket.org/collabspot/office365-rest-client',
      author='Collabspot',
      author_email='aldwyn@collabspot.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'requests>=2.11.1'
      ],
      zip_safe=False)
