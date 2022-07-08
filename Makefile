.PHONY: test format lint

test:
	pytest --exitfirst

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