# coding: utf-8
from setuptools import setup

setup(
  name='fsoi',
  version='0.1',
  description='Forecast Sensitivity - Observational Impact',
  author='Rahul Mahajan',
  author_email='rahul.mahajan@noaa.gov',
  maintainer='David Hahn',
  maintainer_email='hahnd@ucar.edu',
  packages=['fsoi', 'fsoi.ingest', 'fsoi.ingest.emc', 'fsoi.ingest.gmao', 'fsoi.ingest.jma',
            'fsoi.ingest.met', 'fsoi.ingest.meteofr', 'fsoi.ingest.nrl', 'fsoi.plots', 'fsoi.stats',
            'fsoi.web'],
  requires=['pyyaml', 'boto3', 'botocore', 'certifi', 'matplotlib', 'numpy', 'pandas', 'requests',
            'urllib3', 'pyyaml', 'fortranformat'],
  package_dir={'fsoi': 'src/fsoi'},
  package_data={
    'fsoi': ['resources/fsoi/ingest/nrl/*.yaml']
  },
  include_package_data=True,
  zip_safe=False,
  entry_points={
    'console_scripts': [
      'download_nrl=fsoi.ingest.nrl.download_nrl:main',
      'process_nrl=fsoi.ingest.nrl.process_nrl:process_only',
      'ingest_nrl=fsoi.ingest.nrl.__init__:download_and_process_nrl',

      'ingest_gmao=fsoi.ingest.gmao.ingest_gmao:main',
      'convert_gmao=fsoi.ingest.gmao.convert_gmao:main',
      'batch_wrapper=fsoi.web.batch_wrapper:main'
    ]
  }
)

# python setup.py build --build-base build bdist_egg --dist-dir dist
