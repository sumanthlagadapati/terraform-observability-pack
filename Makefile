.PHONY: install test lint format build clean

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src/ tests/
	black --check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

build:
	python -m build

clean:
	rm -rf dist/ build/ *.egg-info/ .mypy_cache/ .pytest_cache/ .ruff_cache/
