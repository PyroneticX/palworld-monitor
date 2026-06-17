.PHONY: run test setup

run:
	.venv\\Scripts\\python.exe -m src.main

test:
	.venv\Scripts\python.exe -m pytest

setup:
	python -m venv .venv
	.venv\Scripts\pip.exe install -r requirements.txt
