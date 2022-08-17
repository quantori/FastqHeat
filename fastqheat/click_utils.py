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
