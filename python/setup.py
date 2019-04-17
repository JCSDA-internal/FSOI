# coding: utf-8
import os.path
import io
import re

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, 'src/fsoi', '__init__.py'), encoding='utf8') as version_file:
  metadata = dict(re.findall(r"""__([a-z]+)__ = "([^"]+)""", version_file.read()))

setup(
  name='fsoi',
  version=metadata['version'],
  description='JCSDA - Command Line Tools',
  author='Rahul Mahajan',
  author_email='rahul.mahajan@noaa.gov',
  maintainer='David Hahn',
  maintainer_email='hahnd@ucar.edu',
  packages=['fsoi', 'fsoi.ingest', 'fsoi.ingest.emc', 'fsoi.ingest.gmao', 'fsoi.ingest.jma',
            'fsoi.ingest.met', 'fsoi.ingest.meteofr', 'fsoi.ingest.nrl', 'fsoi.plots', 'fsoi.stats',
            'fsoi.web'],
  requires=['pyyaml', 'boto3', 'botocore', 'certifi', 'matplotlib', 'numpy', 'pandas', 'requests',
            'urllib3', 'pyyaml'],
  package_dir={'fsoi': 'src/fsoi'},
  package_data={'fsoi': ['resources/*.yaml']},
  include_package_data=True,
  zip_safe=False,
  entry_points={
    'console_scripts': [
      'summary_fsoi=fsoi.plots.summary_fsoi:summary_fsoi_main'
    ]
  }
)

# python setup.py build --build-base build bdist_egg --dist-dir dist
