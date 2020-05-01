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
  packages=['fsoi', 'fsoi.data', 'fsoi.ingest', 'fsoi.ingest.emc', 'fsoi.ingest.gmao', 'fsoi.ingest.jma',
            'fsoi.ingest.met', 'fsoi.ingest.meteofr', 'fsoi.ingest.nrl', 'fsoi.plots', 'fsoi.stats',
            'fsoi.web', 'fsoi.ingest.merra'],
  requires=['bokeh', 'pyyaml', 'boto3', 'botocore', 'certifi',
            'matplotlib', 'numpy', 'pandas', 'requests',
            'urllib3', 'tables', 'fortranformat', 'netCDF4', 'phantomjs', 'selenium'],
  package_dir={'fsoi': 'src/fsoi'},
  package_data={
    'fsoi': [
      'ingest/nrl/*.yaml',
      'ingest/gmao/*.yaml',
      'ingest/met/*.yaml',
      'ingest/merra/*.yaml',
      'data/*.yaml',
      '*.yaml'
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
      'process_met=fsoi.ingest.met.process_met:main',
      'process_merra=fsoi.ingest.merra.process_merra:main',
      'batch_merra=fsoi.ingest.merra.process_merra:batch'
    ]
  }
)

# python setup.py build --build-base build bdist_egg --dist-dir dist
