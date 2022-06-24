.PHONY: test format lint

test:
	# Silences pytest's exit code 5 (i.e. if no tests were collected)
	# TODO: remove when we add tests
	pytest --exitfirst; exit $$(( $$? == 5 ? 0 : $$? ))

format:
	black . && isort .

lint:
	black --check . && isort --check . && flake8 .
