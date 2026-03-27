.POSIX:

#Serial 202602192200
# This makefile is intended to enable Python repositories.

## Recommended .gitignore additions:
# .python

## Override any of the below ?= variables in .config.mk
## You MUST provide the following, POSIX make will not error
# CONTAINER_REGISTRY
# CONTAINER_ORG
# CONTAINER_REPO
-include .config.include.mk

## If you have any local to your repository modifications or extensions
## for this makefile load them into local.mk
## A good usecase would be creating another .check-env:: that looks for
## specific specific-to-the-repo related environment variables
-include local.include.mk

## These are all variables that we might want to override
## only when executed by a CI system.
## We are using this pattern because GitHub Action's make is POSIX standard
## which means no if* conditionals
## These only get set if the values aren't already set
CONTAINER_SWITCHES ?= --rm -it
HADOLINT_FORMAT ?= --format tty
RUFF_OUTPUT ?= full
PYTEST_OUTPUT ?=
$(info If CI_MAKE_OVERRIDES set, including: $(CI_MAKE_OVERRIDES))
-include $(CI_MAKE_OVERRIDES)

DEFAULT_CLEAN_PATHS ?= *.zip *.backup ## Default paths for the main clean target
CLEAN_PATHS ?= ## Overrideable extra paths for cleanup
DOCS_DIR ?= docs
TEST_ARTIFACTS_DIR ?= test-results

# General Container related settings
CONTAINER_ENGINE ?= docker ## Commands will be executed via the container engine, expected to be docker cli compatible
CONTAINER_FILE ?= Containerfile
CONTAINER_WORK_DIR ?= /data

# Python working container related settings
PYTHON_VERSION ?= 3.14
PROJECT_FILE ?= pyproject.toml
PY_CONTAINER_IMAGE ?= ghcr.io/astral-sh/uv
PY_CONTAINER_VERSION ?= python$(PYTHON_VERSION)-alpine ## Override this in .config.mk to pin an image
PY_CONTAINER_SHELL ?= /bin/ash

# Package information
$(info Gathered build information:)
GIT_REF = $(shell git rev-parse --short HEAD)
$(info - GIT_REF = $(GIT_REF))
BUILDSTAMP = $(shell date +%Y%m%dT%H%MZ)
$(info - BUILDSTAMP = $(BUILDSTAMP))
PACKAGE_VERSION ?= $(shell git describe --tags --always --dirty)
$(info - PACKAGE_VERSION = $(PACKAGE_VERSION))
CONTAINER_URI ?= $(CONTAINER_REGISTRY)/$(CONTAINER_ORG)/$(CONTAINER_REPO)
$(info - CONTAINER_URI = $(CONTAINER_URI))

# Labels for container build
CONTAINER_LABELS += --label="org.opencontainers.image.created=$(BUILDSTAMP)"
CONTAINER_LABELS += --label="org.opencontainers.image.revision=$(GIT_REF)"
CONTAINER_LABELS += --label="org.opencontainers.image.version=$(CONTAINER_BASE_TAG)"

CONTAINER_BASE_TAG = $(PACKAGE_VERSION)-$(BUILDSTAMP)
CONTAINER_ALT_TAGS = $(PACKAGE_VERSION) $(PACKAGE_VERSION)-$(GIT_REF) $(EXTRA_CONTAINER_TAG)
CONTAINER_PRIMARY_TAG = $(CONTAINER_URI):$(CONTAINER_BASE_TAG)

# Helper switches for the BASE_COMMAND
BASE_ENV = -e UV_LINK_MODE=copy
BASE_WORKDIR = -w $(CONTAINER_WORK_DIR) -v "$(CURDIR)":$(CONTAINER_WORK_DIR):Z

# Container based commands to for use handling target steps
BASE_COMMAND = $(CONTAINER_ENGINE) run $(CONTAINER_SWITCHES) $(BASE_ENV) $(BASE_WORKDIR)
PY_COMMAND = $(BASE_COMMAND) $(PY_CONTAINER_IMAGE):$(PY_CONTAINER_VERSION)
UV_COMMAND = $(PY_COMMAND) uv

COMPOSE_COMMAND = $(CONTAINER_ENGINE) compose -f compose.defaults.yaml -f $(COMPOSE_CONFIG)

.PHONY: all
all: help

# This helper function makes debuging much easier.
.PHONY: debug-%
.SILENT: "debug-%
debug-%:              ## Debug a variable by calling `make debug-VARIABLE`
	echo '$(*) = "$($(*))"'

.PHONY: .check-env
.SILENT: .check-env
.check-env:
	echo "Checking environment for dependencies..."
	if [ "$(shell which $(CONTAINER_ENGINE))" = "" ]; then echo 'ERROR: `$(CONTAINER_ENGINE)` must be installed and available.'; exit 10; else echo "Found container engine $$(which $(CONTAINER_ENGINE))"; fi

.PHONY: help
.SILENT: help
help:   ## Show this help, includes list of all actions.
	awk 'BEGIN {FS = ":.*?## "}; /^.+: .*?## / && !/awk/ {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' ${MAKEFILE_LIST}

.PHONY: clean
clean: ## Cleanup the local checkout
	-rm -rf $(DEFAULT_CLEAN_PATHS) $(CLEAN_PATHS)

.SILENT: $(DOCS_DIR)
$(DOCS_DIR):
	echo "Initializing $(@)"
	mkdir -p $(@)

.SILENT: $(TEST_ARTIFACTS_DIR)
$(TEST_ARTIFACTS_DIR):
	echo "Initializing $(@)"
	mkdir -p $(@)

.PHONY: init
setup:  ## Used to initialize repository by loading dependencies
	$(UV_COMMAND) sync $(UV_OUTPUT)

.PHONY: format
format: init ## Format code with uv/ruff
	$(UV_COMMAND) format

format-check: init ## Check code formatting without making changes
	$(UV_COMMAND) format --check

.PHONY: lint
lint: format-check lint-py lint-container ## Standard entry point for running linters.

.PHONY: lint-container
lint-container: $(TEST_ARTIFACTS_DIR) ## Entrypoint for running linter on the container file
	$(CONTAINER_ENGINE) run --rm $(CONTAINER_SWITCH) ghcr.io/hadolint/hadolint hadolint $(HADOLINT_FORMAT) - < $(CONTAINER_FILE) $(HADOLINT_OUTPUT)

.PHONY: lint-py
lint-py: $(TEST_ARTIFACTS_DIR) ## Entrypoint for running node linter
	$(UV_COMMAND) run ruff check . $(RUFF_RESULTS)

.PHONY: test
test: test-unit test-integration test-coverage ## Standard entry point for running all tests.
	#echo "Running tests"

.PHONY: test-coverage
test-coverage: ## Looks at overall coverage
	$(UV_COMMAND) run coverage $(COVERAGE_OUTPUT)

.PHONY: test-unit
test-unit: $(TEST_ARTIFACTS_DIR) ## Run unit tests (no infrastructure required)
	$(UV_COMMAND) run pytest tests/unit $(PYTEST_UNIT_OUTPUT)

.container: Containerfile.test
	$(CONTAINER_ENGINE) build -t chapter-mp3s-test -f Containerfile.test .
	$(CONTAINER_ENGINE) inspect --format='{{.Id}}' chapter-mp3s-test > .container

.PHONY: test-integration
test-integration: .container $(TEST_ARTIFACTS_DIR) ## Run integration tests (requires ffmpeg via test container)
	$(BASE_COMMAND) chapter-mp3s-test uv run pytest tests/integration $(PYTEST_INTEGRATION_OUTPUT)

.PHONY: repl
repl: ## To enter Python REPL interactively
	$(PY_COMMAND) python

.PHONY: shell
shell: ## To interactively enter the container in a shell
	$(PY_COMMAND) $(PY_CONTAINER_SHELL)

.PHONY: update
update: ## Will refresh the python dependencies locally installed to match `pyproject.toml`
	make init

.PHONY: update-dependencies
update-dependencies: ## Run command to update dependencies in `pyproject.toml`
	$(UV_COMMAND) sync --upgrade $(UV_OUTPUT)

.PHONY: build
build: build-python build-container ## Run all builds

.PHONY: build-python
build-python:  ## Build python artifacts
	$(UV_COMMAND) build

.PHONY: build-container
build-container: ## Build container with the latest version of the current program
	$(CONTAINER_ENGINE) build -t $(CONTAINER_PRIMARY_TAG) -f $(CONTAINER_FILE) $(CONTAINER_LABELS) .
	for TAG in $(CONTAINER_ALT_TAGS); do \
		$(CONTAINER_ENGINE) tag $(CONTAINER_PRIMARY_TAG) $(CONTAINER_URI):$${TAG}; \
	done

.PHONY: publish-container
publish-container: build-container ## Push current image to remote registry
	$(CONTAINER_ENGINE) push $(CONTAINER_PRIMARY_TAG)
	for TAG in $(CONTAINER_ALT_TAGS); do \
		$(CONTAINER_ENGINE) push $(CONTAINER_URI):$${TAG}; \
	done
