# Development guide

Development happens on the `dev` branch. `master` is the stable branch.

Clone the project, enter the project directory, and switch to the development branch:

```bash
~$ git clone git@github.com:quantori/FastqHeat.git
~$ cd FastqHeat/
~/FastqHeat$ git checkout dev
```

Install dependencies with [`poetry`](https://python-poetry.org/):

```bash
~/FastqHeat$ poetry install  # NOTE: includes dev dependencies
```

Make sure you've installed optional command-line utilities as well.
If you add new Python dependencies, they should be included in
[`pyproject.toml`](pyproject.toml) in the relevant sections (don't forget
to recreate `poetry.lock` after you're done). All new non-Python dependencies
should be documented in [README.md](README.md).

To check that everything is in order:

```bash
~/FastqHeat$ make format  # Formats code
~/FastqHeat$ make lint  # Runs linters against code
~/FastqHeat$ make test  # Runs unit tests
```
