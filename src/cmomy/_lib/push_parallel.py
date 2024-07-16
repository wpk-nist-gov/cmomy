"""Vectorized pushers."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import numba as nb

from . import _push
from .decorators import myguvectorize

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from ..typing import FloatT, NDGeneric


_PARALLEL = True  # Auto generated from push.py
_decorator = partial(myguvectorize, parallel=_PARALLEL)


@_decorator(
    "(),(),(mom)",
    [
        (nb.float32, nb.float32, nb.float32[:]),
        (nb.float64, nb.float64, nb.float64[:]),
    ],
)
def push_val(x: NDGeneric[FloatT], w: NDGeneric[FloatT], out: NDArray[FloatT]) -> None:
    _push.push_val(x, w, out)


@_decorator(
    "(sample),(sample),(mom)",
    [
        (nb.float32[:], nb.float32[:], nb.float32[:]),
        (nb.float64[:], nb.float64[:], nb.float64[:]),
    ],
)
def reduce_vals(x: NDArray[FloatT], w: NDArray[FloatT], out: NDArray[FloatT]) -> None:
    for i in range(x.shape[0]):
        _push.push_val(x[i], w[i], out)


@_decorator(
    "(mom),(mom)",
    signature=[
        (nb.float32[:], nb.float32[:]),
        (nb.float64[:], nb.float64[:]),
    ],
)
def push_data(data: NDArray[FloatT], out: NDArray[FloatT]) -> None:
    _push.push_data(data, out)


@_decorator(
    "(sample, mom),(mom)",
    [
        (nb.float32[:, :], nb.float32[:]),
        (nb.float64[:, :], nb.float64[:]),
    ],
)
def reduce_data(data: NDArray[FloatT], out: NDArray[FloatT]) -> None:
    for i in range(data.shape[0]):
        _push.push_data(data[i, :], out)


@_decorator(
    "(sample, mom) -> (mom)",
    [
        (nb.float32[:, :], nb.float32[:]),
        (nb.float64[:, :], nb.float64[:]),
    ],
    writable=None,
)
def reduce_data_fromzero(
    data: NDArray[FloatT],
    out: NDArray[FloatT],
) -> None:
    out[...] = 0.0
    for i in range(data.shape[0]):
        _push.push_data(data[i, :], out)


@_decorator(
    "(sample, mom) -> (sample, mom)",
    [
        (nb.float32[:, :], nb.float32[:, :]),
        (nb.float64[:, :], nb.float64[:, :]),
    ],
    writable=None,
)
def cumulative(
    data: NDArray[FloatT],
    out: NDArray[FloatT],
) -> None:
    out[0, ...] = data[0, ...]
    for i in range(1, data.shape[0]):
        out[i, ...] = data[i, ...]
        _push.push_data(out[i - 1, ...], out[i, ...])


@_decorator(
    "(sample, mom) -> (sample, mom)",
    [
        (nb.float32[:, :], nb.float32[:, :]),
        (nb.float64[:, :], nb.float64[:, :]),
    ],
    writable=None,
)
def cumulative_inverse(
    data: NDArray[FloatT],
    out: NDArray[FloatT],
) -> None:
    out[0, ...] = data[0, ...]
    for i in range(1, data.shape[0]):
        out[i, ...] = data[i, ...]
        _push.push_data_scale(data[i - 1, ...], -1.0, out[i, ...])
