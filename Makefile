.PHONY: install clean build run test dist

# Default target
all: test build

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Clean up build and distribution files
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete

# Build the package
build:
	python setup.py build

# Run the application
run:
	python main.py

# Run tests
test:
	pytest

# Create distribution packages
dist: clean
	python setup.py sdist bdist_wheel

# Install the package for development
dev:
	pip install -e .
