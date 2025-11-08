.PHONY: help install test lint format clean docker-build docker-up docker-down docker-logs

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=. --cov-report=html --cov-report=term

lint: ## Run linters
	flake8 .
	mypy . --ignore-missing-imports || true
	black --check .
	isort --check-only .

format: ## Format code
	black .
	isort .

clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-restart: ## Restart Docker containers
	docker-compose restart

docker-shell: ## Access Docker container shell
	docker-compose exec bot bash

run: ## Run bot locally
	python main.py

run-webhook: ## Run bot with webhook
	python main_webhook.py

