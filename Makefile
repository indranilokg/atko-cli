.PHONY: help clean dev package test

help:
	@echo "This project assumes that an active Python virtualenv is present."
	@echo "The following make targets are available:"
	@echo "	 dev 	install all deps for dev env"
	@echo "	 test	run all tests with coverage"

clean:
	@echo "+ $@"
	@find . -type f -name '*.pyc' -exec rm -f {} +
	@find . -type d -name '*__pycache__*' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type d -name '*egg-info' -exec rm -rf {} +
	rm -rf dist/*

dev:
	@echo "+ $@"
	pip install -r requirements.txt
	pip install -e .

package:
	@echo "+ $@"
	python setup.py sdist
	python setup.py bdist_wheel

test:
	@echo "+ $@"
	coverage run -m pytest
	coverage html

lint:
	@echo "+ $@"
	flake8 . --count --statistics