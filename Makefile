.PHONY: test format lint

test:
	pytest --exitfirst

format:
	black . && isort .

lint:
	black --check . && isort --check . && flake8 .
