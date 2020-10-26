VENV = venv

.PHONY: help clean dev package test

help:
	@echo "This project assumes that an active Python virtualenv is present."
	@echo "The following make targets are available:"
	@echo "	 dev 	install all deps for dev env"
	@echo "	 test	run all tests with coverage"

install: requirements.txt
	@echo "+ $@"
	python3 -m venv $(VENV)

clean-venv:
	@echo "+ $@"
	rm -rf $(VENV)

clean-dev-full:
	@echo "+ $@"
	rm -rf ~/.atkocli

clean:
	@echo "+ $@"
	@find . -type f -name '*.pyc' -exec rm -f {} +
	@find . -type d -name '*__pycache__*' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type d -name '*egg-info' -exec rm -rf {} +
	rm -rf dist/*

dev:
	@echo "+ $@"
	$(VENV)/bin/pip install -r requirements.txt --upgrade
	$(VENV)/bin/pip install -e .
	@echo "+ "
	@echo "Do not forgot to 'source venv/bin/active'"

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