import logging
import subprocess
import typing as tp

import click


class OrderableOption(click.Option):
    @tp.no_type_check
    def __init__(self, *args, order: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = order


class OrderedOptsCommand(click.Command):
    def get_params(self, ctx: click.Context) -> list[click.Parameter]:
        params = super().get_params(ctx)
        return sorted(params, key=lambda x: getattr(x, 'order', 10000))


def check_binary_available(
    program_name: str,
    exception_cls: tp.Type[Exception] = click.UsageError,
    exception_kwargs: tp.Optional[dict] = None,
) -> None:
    if exception_kwargs is None:
        exception_kwargs = dict()
    try:
        subprocess.run([program_name, '--version'], text=True, capture_output=True, check=True)
    except FileNotFoundError as exc:
        raise exception_cls(
            f"""Unable to run "{program_name}": File not found.""",
            **exception_kwargs,  # noqa
        ) from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr or exc.stdout
        logging.error(message)
        raise exception_cls(
            f"""Unable to run "{program_name}": {message}""", **exception_kwargs  # noqa
        ) from exc
