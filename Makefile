.PHONY: clean clean-test clean-pyc clean-build help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache




################################################################################
# utilities
################################################################################
.PHONY: lint pre-commit-init pre-commit-run pre-commit-run-all init

lint: ## check style with flake8
	flake8 cmomy tests

pre-commit-init: ## install pre-commit
	pre-commit install

pre-commit-run: ## run pre-commit
	pre-commit run

pre-commit-run-all: ## run pre-commit on all files
	pre-commit run --all-files

.git: ## init git
	git init

init: .git pre-commit-init ## run git-init pre-commit


################################################################################
# virtual env
################################################################################
.PHONY: conda-env conda-dev conda-all mamba-env mamba-dev mamba-all activate


# environment-dev.yml: environment.yml environment-tools.yml
# 	conda-merge environment.yml environment-tools.yml > environment-dev.yml

environment-dev.yml: environment.yml environment-tools.yml
	conda-merge environment.yml environment-tools.yml > environment-dev.yml


# conda-env: ## conda create base env
# 	conda env create -f environment.yml

# conda-dev: ## conda update development dependencies
# 	conda env update -n cmomy-env -f environment-dev.yml

# conda-all: conda-env conda-dev ## conda create development env

mamba-env: ## mamba create base env
	mamba env create -f environment.yml

mamba-dev: ## mamba update development dependencies
	mamba env create -f environment-dev.yml

mamba-env-update:
	mamba env update -f environment.yml

mamba-dev-update:
	mamba env update -f environment-dev.yml


activate: ## activate base env
	conda activate cmomy-env


################################################################################
# my convenience functions
################################################################################
.PHONY: user-venv user-autoenv-zsh user-all
user-venv: ## create .venv file with name of conda env
	echo cmomy-env > .venv

user-autoenv-zsh: ## create .autoenv.zsh files
	echo conda activate cmomy-env > .autoenv.zsh
	echo conda deactivate > .autoenv_leave.zsh

user-all: user-venv user-autoenv-zsh ## runs user scripts


################################################################################
# Testing
################################################################################
.PHONY: test test-all coverage
test: ## run tests quickly with the default Python
	pytest -x -v

test-gen_examples:
	pytest -x -v --accept

test-all: ## run tests on every Python version with tox
	tox -- -x -v


coverage: ## check code coverage quickly with the default Python
	coverage run --source cmomy -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html



.PHONY: version-scm version-import version
version-scm: ## check version of package
	python -m setuptools_scm

version-import: ## check version from python import
	python -c 'import cmomy; print(cmomy.__version__)'

version: version-scm version-import


################################################################################
# Docs
################################################################################

.PHONY: create-docs-nist-pages
# create docs-nist-pages directory with empty branch
create-docs-nist-pages:
	mkdir -p docs-nist-pages ; \
	cd docs-nist-pages ; \
	echo git clone git@github.com:usnistgov/cmomy.git html ;\
	echo "To push, use the following" ; \
	echo "cd docs-nist-pages/html" ; \
	echo "" ; \
	echo git checkout --orphan nist-pages ; \
	echo git reset --hard ; \
	echo git commit --allow-empty -m "Initializing gh-pages branch" ; \
	echo git push origin nist-pages ; \
	echo git checkout master ; \


.PHONY: docs serverdocs doc-spelling docs-nist-pages
docs: ## generate Sphinx HTML documentation, including API docs
	rm -fr docs/generated
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

docs-spelling:
	sphinx-build -b spelling docs docs/_build

docs-nist-pages:
	tox -e docs


################################################################################
# distribution
################################################################################

.PHONY: pypi-build pypi-release pypi-test-release pypi-dist
pypi-build:
	tox -e pypi-build

pypi-release:
	tox -e pypi-release


pypi-test-release:
	tox -e pypi-test-release

pypi-dist:
	pypi-build
	pypi-release

.PHONY: conda-grayksull conda-build conda-release conda-dist

conda-grayskull:
	tox -e grayskull

conda-build:
	tox -e conda-build

conda-release:
	echo 'prefix upload with .tox/conda-dist/'

conda-dist:
	conda-grayskull
	conda-build
	conda-release


################################################################################
# installation
################################################################################
.PHONY: install install-dev
install: ## install the package to the active Python's site-packages (run clean?)
	pip install .

install-dev: ## install development version (run clean?)
	pip install -e . --no-deps
