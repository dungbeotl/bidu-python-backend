.PHONY: run dev setup clean test docker help

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup  - Create virtual environment and install dependencies"
	@echo "  make dev    - Run application in development mode with hot-reload"
	@echo "  make run    - Run application without hot-reload"
	@echo "  make test   - Run tests"
	@echo "  make clean  - Clean up cache files"
	@echo "  make docker - Build and run Docker container"

# Setup environment
setup:
	python3 -m venv venv
	. venv/bin/activate && pip3 install -r requirements.txt

# Update dependencies
update-deps:
	pip3 install -U -r requirements.txt

# Run in development mode
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run without hot-reload
run:
	uvicorn main:app --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest

# Clean up cache files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

# Docker build and run
docker:
	docker-compose up --build