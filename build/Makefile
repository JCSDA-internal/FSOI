PYTHON_VERSION=3.7

all: egg
	@echo "Success"

install: egg
	cd ../python; easy_install-${PYTHON_VERSION} --user dist/fsoi-0.1-py${PYTHON_VERSION}.egg

aws_lambda:
	rm -Rf artifact_build && mkdir artifact_build
	cd artifact_build; pip3 install -t . chardet==3.0.4 requests==2.23.0 urllib3==1.25.9 certifi==2020.4.5.1 idna==2.9 pandas==1.0.3 pytz==2020.1 six==1.14.0 pyyaml==5.3.1 matplotlib==3.2.1 pyparsing==2.4.7 cycler==0.10.0 kiwisolver==1.2.0 numexpr==2.7.1 Pillow==7.1.2 tables==3.6.1
	cd artifact_build; rm -Rf *.dist-info __pycache__ bin setuptools
	cd artifact_build; pwd
	cd artifact_build; cp -R ../../python/src/fsoi .
	cd artifact_build; ln -s fsoi/ingest/nrl/ingest_navy.py .
	cd artifact_build; ln -s fsoi/ingest/gmao/ingest_gmao.py .
	cd artifact_build; ln -s fsoi/web/lambda_wrapper.py .
	cd artifact_build; find . -type f -name \*.py -exec chmod ugo+rx {} \;
	cd artifact_build; find . -type f -exec chmod ugo+r {} \;
	cd artifact_build; find . -type d -exec chmod ugo+rx {} \;
	cd artifact_build; tar -cvzf ../fsoi_lambda.zip .

egg:
	cd ../python; python3 setup.py build --build-base build bdist_egg --dist-dir dist

clean:
	cd ../python; rm -Rf dist build fsoi.egg-info
