# Development guide

Development happens on the `dev` branch. `master` is the stable branch.

Clone the project, enter the project directory, and switch to the development branch:

```bash
~$ git clone git@github.com:quantori/FastqHeat.git
~$ cd FastqHeat/
~/FastqHeat$ git checkout dev
```

Install [`poetry`](https://python-poetry.org/), then install the project:

```bash
~/FastqHeat$ poetry install  # NOTE: includes dev dependencies
```

> **NOTE**: to run commands within the project's virtual environment you will have
> to activate Poetry's shell (`poetry shell`) or run them via `poetry run`. If that
> sounds too complicated, install the project via `pip` in editable mode (`-e`)
> instead, and then install project's dependencies with `poetry install --no-root`.

Make sure you've installed optional command-line utilities as well.
If you add new Python dependencies, they should be included in
[`pyproject.toml`](pyproject.toml) in the relevant sections (don't forget
to recreate [`poetry.lock`](poetry.lock) after you're done). All new
non-Python dependencies should be documented in [README.md](README.md).

To check that everything is in order:

```bash
~/FastqHeat$ make format  # Formats code
~/FastqHeat$ make lint  # Runs linters against code
~/FastqHeat$ make test  # Runs unit tests
```
