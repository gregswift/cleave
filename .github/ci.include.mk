## This file exists specifically to allow overriding of variables
## when running via GitHub Actions.  The workflows need to globally define:
## env:
##   CI_MAKE_OVERRIDES: .github/ci-overrides.mk
$(info Overriding variables for CI environment)
COMPOSE_CONFIG = compose.ci.yaml
CONTAINER_SWITCHES = --rm
HADOLINT_FORMAT = --format sarif
HADOLINT_OUTPUT = | tee $(TEST_ARTIFACTS_DIR)/container-lint.sarif
RUFF_OUTPUT = --output-format=sarif | tee $(TEST_ARTIFACTS_DIR)/ruff-lint.sarif
PYTEST_OUTPUT_PREFIX = --junitxml=$(TEST_ARTIFACTS_DIR)/
PYTEST_UNIT_OUTPUT = $(PYTEST_OUTPUT_PREFIX)/pytest-unit.xml
PYTEST_INTEGRATION_OUTPUT = $(PYTEST_OUTPUT_PREFIX)/pytest-integration.xml
UV_OUTPUT = --no-progress
