PYTHON_VERSION=3.7

all: egg
	@echo "Success"

install: egg
	cd ../python; easy_install-${PYTHON_VERSION} --user dist/fsoi-0.1-py${PYTHON_VERSION}.egg

egg:
	cd ../python/src/fsoi; ln -s ../../resources .
	cd ../python; python3 setup.py build --build-base build bdist_egg --dist-dir dist
	rm -f ../python/src/fsoi/resources

clean:
	cd ../python; rm -Rf dist build fsoi.egg-info