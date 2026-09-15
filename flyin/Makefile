PYTHON = python3
PIP = $(PYTHON) -m pip

.PHONY: install lint typecheck test clean

install:
	$(PIP) install -r requirements.txt

lint:
	flake8 . --exclude .venv

typecheck:
	mypy . --strict --exclude .venv

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete