import typing as tp
from os import PathLike

PathType = tp.Union[str, PathLike]
JsonDict = tp.Dict[
    str, tp.Any
]  # https://github.com/python/typing/issues/182#issuecomment-185996450
