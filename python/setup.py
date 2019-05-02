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
            'urllib3', 'pyyaml', 'fortranformat', 'netCDF4'],
  package_dir={'fsoi': 'src/fsoi'},
  package_data={
    'fsoi': [
      'resources/fsoi/ingest/nrl/*.yaml',
      'resources/fsoi/ingest/gmao/*.yaml'
    ]
  },
  include_package_data=True,
  zip_safe=False,
  entry_points={
    'console_scripts': [
      'download_nrl=fsoi.ingest.nrl.download_nrl:main',
      'process_nrl=fsoi.ingest.nrl.process_nrl:main',
      'ingest_nrl=fsoi.ingest.nrl.__init__:download_and_process_nrl',

      'download_gmao=fsoi.ingest.gmao.download_gmao:main',
      'process_gmao=fsoi.ingest.gmao.process_gmao:main',
      'ingest_gmao=fsoi.ingest.gmao.__init__:download_and_process_gmao',

      'process_stats=fsoi.stats.process_stats:main',
      'batch_wrapper=fsoi.web.batch_wrapper:main'
    ]
  }
)

# python setup.py build --build-base build bdist_egg --dist-dir dist
