.PHONY: test audit freeze check demo clean

PYTHON ?= python3
ROOT ?= $(CURDIR)

test:
	PYTHONPATH=$(ROOT) $(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

audit:
	PYTHONPATH=$(ROOT) $(PYTHON) tests/audit_harness.py

freeze:
	PYTHONPATH=$(ROOT) $(PYTHON) tests/golden_check.py --freeze

check:
	PYTHONPATH=$(ROOT) $(PYTHON) tests/golden_check.py --check

demo:
	PYTHONPATH=$(ROOT) $(PYTHON) -m blindspot demo

clean:
	rm -rf .blindspot __pycache__ blindspot/__pycache__ tests/__pycache__ .pytest_cache
