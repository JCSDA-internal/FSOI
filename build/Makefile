PYTHON_VERSION=3.7

all: egg
	@echo "Success"

install: egg
	cd ../python; easy_install-${PYTHON_VERSION} --user dist/fsoi-0.1-py${PYTHON_VERSION}.egg

aws_lambda:
	rm -Rf artifact_build && mkdir artifact_build
	cd artifact_build; pip3 install -t . chardet requests urllib3 certifi idna pandas pytz six pyyaml matplotlib pyparsing cycler kiwisolver numexpr mock tables
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
