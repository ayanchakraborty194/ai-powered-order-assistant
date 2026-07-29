PYTHON ?= python3.11
VENV_DIR ?= .venv

.PHONY: setup install-dev test run

setup: install-dev
	@echo "Developer environment is ready."

install-dev:
	@test -d "$(VENV_DIR)" || $(PYTHON) -m venv "$(VENV_DIR)"
	@"$(VENV_DIR)/bin/python" -m pip install --upgrade pip && "$(VENV_DIR)/bin/python" -m pip install -e ".[dev]"

test:
	@"$(VENV_DIR)/bin/pytest" app/tests -v

run:
	@"$(VENV_DIR)/bin/uvicorn" app.main:app --reload --port 8000
