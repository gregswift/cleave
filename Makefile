.PHONY: install test test-unit test-integration lint fmt typecheck build clean

install:
	pip install -e ".[dev]"

test:
	pytest --cov=chapter_mp3s --cov-report=term-missing

test-unit:
	pytest -m "not integration" --cov=chapter_mp3s --cov-report=term-missing

test-integration:
	pytest -m integration -v

lint:
	ruff check src tests

fmt:
	ruff format src tests
	ruff check --fix src tests

typecheck:
	mypy src

check: lint typecheck test-unit

build:
	pip install hatch && hatch build

clean:
	rm -rf dist/ build/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
