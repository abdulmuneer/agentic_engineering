PYTHON ?= python3

.PHONY: test validate check

test:
	$(PYTHON) -m unittest discover -v

validate:
	$(PYTHON) -m agentic_engineering.runtime validate-framework agentic_engineering --strict
	$(PYTHON) -m agentic_engineering.runtime validate agentic_engineering/examples/fornax --strict

check:
	$(PYTHON) -m py_compile agentic_engineering/runtime/*.py
	$(MAKE) test
	$(MAKE) validate
