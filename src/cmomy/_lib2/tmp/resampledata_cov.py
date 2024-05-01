# mypy: disable-error-code="no-untyped-call,no-untyped-def"
"""Vectorized pushers."""

from __future__ import annotations

from functools import partial

import numba as nb

from . import pushscalar_cov
from .utils import myguvectorize, myjit

_PARALLEL = False
_vectorize = partial(myguvectorize, parallel=_PARALLEL)
_jit = partial(myjit, parallel=_PARALLEL)


# NOTE: The parallel implementation is quite similar to the old
# way of doing things (with reshape and njit), but the serial is slower.
# Still, this is way simpler...


@_vectorize(
    "(sample,mom0,mom1),(replicate,sample),(replicate,mom0,mom1)",
    [
        (nb.float32[:, :, :], nb.float32[:, :], nb.float32[:, :, :]),
        (nb.float64[:, :, :], nb.float64[:, :], nb.float64[:, :, :]),
    ],
)
def resample_data(other, freq, data) -> None:
    nrep, nsamp = freq.shape

    assert other.shape[1:] == data.shape[1:]
    assert other.shape[0] == nsamp
    assert data.shape[0] == nrep

    for isamp in range(nsamp):
        for irep in range(nrep):
            f = freq[irep, isamp]
            if f == 0:
                continue
            pushscalar_cov.push_data_scale(other[isamp, ...], f, data[irep, ...])


@_vectorize(
    "(sample,mom0,mom1),(replicate,sample),(replicate,mom0,mom1)",
    [
        (nb.float32[:, :, :], nb.float32[:, :], nb.float32[:, :, :]),
        (nb.float64[:, :, :], nb.float64[:, :], nb.float64[:, :, :]),
    ],
)
def resample_data_fromzero(other, freq, data) -> None:
    nrep, nsamp = freq.shape

    assert other.shape[1:] == data.shape[1:]
    assert other.shape[0] == nsamp
    assert data.shape[0] == nrep

    for irep in range(nrep):
        first_nonzero = nsamp
        for isamp in range(nsamp):
            f = freq[irep, isamp]
            if f != 0:
                first_nonzero = isamp
                data[irep, :, :] = other[isamp, :, :]
                data[irep, 0, 0] *= f
                break

        for isamp in range(first_nonzero + 1, nsamp):
            f = freq[irep, isamp]
            if f != 0:
                pushscalar_cov.push_data_scale(other[isamp, ...], f, data[irep, ...])


@_vectorize(
    "(sample,mom0,mom1),(replicate,sample),(replicate,mom0,mom1)",
    [
        (nb.float32[:, :, :], nb.float32[:, :], nb.float32[:, :, :]),
        (nb.float64[:, :, :], nb.float64[:, :], nb.float64[:, :, :]),
    ],
)
def resample_data2(other, freq, data) -> None:
    nrep, nsamp = freq.shape

    assert other.shape[1:] == data.shape[1:]
    assert other.shape[0] == nsamp
    assert data.shape[0] == nrep

    for irep in range(nrep):
        for isamp in range(nsamp):
            f = freq[irep, isamp]
            if f == 0:
                continue
            pushscalar_cov.push_data_scale(other[isamp, ...], f, data[irep, ...])


@_jit(
    # "(sample,val,mom0, mom1),(replicate,sample),(replicate,val,mom0,mom1)",
    [
        (nb.float32[:, :, :, :], nb.float32[:, :], nb.float32[:, :, :, :]),
        (nb.float64[:, :, :, :], nb.float64[:, :], nb.float64[:, :, :, :]),
    ],
)
def resample_data_jit(other, freq, data) -> None:
    nrep, nsamp = freq.shape
    nval = other.shape[1]

    assert other.shape[1:] == data.shape[1:]
    assert other.shape[0] == nsamp
    assert data.shape[0] == nrep

    for irep in nb.prange(nrep):
        for isamp in range(nsamp):
            f = freq[irep, isamp]
            if f == 0:
                continue
            for k in range(nval):
                pushscalar_cov.push_data_scale(
                    other[isamp, k, ...], f, data[irep, k, ...]
                )


@_jit(
    # "(sample,val,mom0, mom1),(replicate,sample),(replicate,val,mom0,mom1)",
    [
        (nb.float32[:, :, :, :], nb.float32[:, :], nb.float32[:, :, :, :]),
        (nb.float64[:, :, :, :], nb.float64[:, :], nb.float64[:, :, :, :]),
    ],
)
def resample_data_fromzero_jit(other, freq, data) -> None:
    nrep, nsamp = freq.shape
    nval = other.shape[1]

    assert other.shape[1:] == data.shape[1:]
    assert other.shape[0] == nsamp
    assert data.shape[0] == nrep

    for irep in nb.prange(nrep):
        first_nonzero = nsamp
        for isamp in range(nsamp):
            f = freq[irep, isamp]
            if f != 0:
                first_nonzero = isamp
                for k in range(nval):
                    data[irep, k, :, :] = other[isamp, k, :, :]
                    data[irep, k, 0, 0] *= f
                break

        for isamp in range(first_nonzero + 1, nsamp):
            f = freq[irep, isamp]
            if f == 0:
                continue
            for k in range(nval):
                pushscalar_cov.push_data_scale(
                    other[isamp, k, ...], f, data[irep, k, ...]
                )
