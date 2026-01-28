.PHONY: help install install-dev test lint format clean docker-build docker-run init example

PYTHON := python3
PIP := pip3

help:
	@echo "MACDS - Multi-Agent Coding Development System"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  init           Initialize MACDS in current directory"
	@echo ""
	@echo "Development:"
	@echo "  test           Run test suite"
	@echo "  test-cov       Run tests with coverage report"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code with black and isort"
	@echo "  typecheck      Run mypy type checking"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-run     Run MACDS in Docker"
	@echo "  docker-dev     Run in development mode with Docker"
	@echo ""
	@echo "Usage:"
	@echo "  example        Run example workflow"
	@echo "  status         Show system status"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean          Remove build artifacts"
	@echo "  clean-all      Remove all generated files"

# Setup targets
install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

install-all:
	$(PIP) install -e ".[all]"

init:
	$(PYTHON) -m macds.main init

# Development targets
test:
	$(PYTHON) -m pytest macds/tests/ -v

test-cov:
	$(PYTHON) -m pytest macds/tests/ -v --cov=macds --cov-report=html

lint:
	$(PYTHON) -m flake8 macds/ --max-line-length=100 --ignore=E501,W503
	$(PYTHON) -m mypy macds/ --ignore-missing-imports

format:
	$(PYTHON) -m black macds/
	$(PYTHON) -m isort macds/

typecheck:
	$(PYTHON) -m mypy macds/ --ignore-missing-imports

# Docker targets
docker-build:
	docker build -t macds:latest .

docker-run:
	docker run -it --rm \
		-v $$(pwd)/workspace:/app/workspace \
		-e OPENROUTER_API_KEY=$${OPENROUTER_API_KEY} \
		macds:latest

docker-dev:
	docker compose --profile dev up macds-dev

docker-shell:
	docker run -it --rm \
		-v $$(pwd):/app \
		-e OPENROUTER_API_KEY=$${OPENROUTER_API_KEY} \
		--entrypoint /bin/bash \
		macds:latest

# Usage targets
example:
	$(PYTHON) -m macds.main example

status:
	$(PYTHON) -m macds.main status

run:
	$(PYTHON) -m macds.main run "$(TASK)"

# Cleanup targets
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage

clean-all: clean
	rm -rf .macds/
