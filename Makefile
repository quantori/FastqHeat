.PHONY: test format lint

test:
	pytest --exitfirst

format:
	pip install -qqq --upgrade black isort && \
	black . && isort .

lint:
	pip install -qqq --upgrade black isort flake8 && \
	black --check . && isort --check . && flake8 .