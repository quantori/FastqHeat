.PHONY: test format lint

test:
	# Silences pytest's exit code 5 (i.e. if no tests were collected)
	# TODO: remove when we add tests
	pytest --exitfirst; exit $$(( $$? == 5 ? 0 : $$? ))

format:
	black . && isort .

lint:
	echo "Checking code format with black..."
	black --check .
	echo "Checking imports order..."
	isort --check .
	echo "Running flake8..."
	flake8 .
	echo "Running mypy..."
	mypy .
	echo "Running safety..."
	safety check --full-report