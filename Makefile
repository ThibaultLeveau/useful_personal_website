PYTHON ?= python

.PHONY: help doctor repo-check verify backend-check frontend-check api-generate api-check seed-demo

help:
	@$(PYTHON) scripts/task.py help

doctor:
	@$(PYTHON) scripts/task.py doctor

repo-check:
	@$(PYTHON) scripts/task.py repo-check

verify:
	@$(PYTHON) scripts/task.py verify

backend-check:
	@$(PYTHON) scripts/task.py backend-check

frontend-check:
	@$(PYTHON) scripts/task.py frontend-check

api-generate:
	@$(PYTHON) scripts/task.py api-generate

api-check:
	@$(PYTHON) scripts/task.py api-check

seed-demo:
	@$(PYTHON) scripts/task.py seed-demo
