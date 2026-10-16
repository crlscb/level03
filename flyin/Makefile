PYTHON = python3
PIP = $(PYTHON) -m pip

.PHONY: install run debug lint typecheck test clean

install:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py

debug:
	$(PYTHON) -m pdb main.py

lint:
	$(PYTHON) -m flake8 . --exclude=.venv

typecheck:
	$(PYTHON) -m mypy . --strict --exclude .venv

test:
	$(PYTHON) -m pytest -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete