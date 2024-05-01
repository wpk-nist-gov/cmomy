# mypy: disable-error-code="no-untyped-call,no-untyped-def"
"""Vectorized pushers."""

from __future__ import annotations

from functools import partial

import numba as nb

from . import pushscalar_cov
from .utils import myguvectorize, myjit

# NOTE: The parallel implementation is quite similar to the old
# way of doing things (with reshape and njit), but the serial is slower.
# Still, this is way simpler...

_PARALLEL = False
_vectorize = partial(myguvectorize, parallel=_PARALLEL)
_jit = partial(myjit, parallel=_PARALLEL)


@_vectorize(
    "(sample),(sample),(sample),(replicate,sample),(replicate,mom0,mom1)",
    [
        (
            nb.float32[:],
            nb.float32[:],
            nb.float32[:],
            nb.float32[:, :],
            nb.float32[:, :, :],
        ),
        (
            nb.float64[:],
            nb.float32[:],
            nb.float32[:],
            nb.float64[:, :],
            nb.float64[:, :, :],
        ),
    ],
)
def resample_vals(w, x0, x1, freq, data) -> None:
    for isamp in range(freq.shape[1]):
        for irep in range(freq.shape[0]):
            f = freq[irep, isamp]
            if f == 0:
                continue
            pushscalar_cov.push_val(w[isamp] * f, x0[isamp], x1[isamp], data[irep, ...])


@_vectorize(
    "(sample),(sample),(sample),(replicate,sample),(replicate,mom0,mom1)",
    [
        (
            nb.float32[:],
            nb.float32[:],
            nb.float32[:],
            nb.float32[:, :],
            nb.float32[:, :, :],
        ),
        (
            nb.float64[:],
            nb.float32[:],
            nb.float32[:],
            nb.float64[:, :],
            nb.float64[:, :, :],
        ),
    ],
)
def resample_vals2(w, x0, x1, freq, data) -> None:
    for irep in range(freq.shape[0]):
        for isamp in range(freq.shape[1]):
            f = freq[irep, isamp]
            if f == 0:
                continue
            pushscalar_cov.push_val(w[isamp] * f, x0[isamp], x1[isamp], data[irep, ...])


# Old (dumb) way of doing things.  Faster is many cases
@_jit(
    # w[samp, value], x0[samp, value], x1[samp, value], freq[rep, samp], out[rep, value, mom0, mom1]
    [
        (
            nb.float32[:, :],
            nb.float32[:, :],
            nb.float32[:, :],
            nb.float32[:, :],
            nb.float32[:, :, :, :],
        ),
        (
            nb.float64[:, :],
            nb.float64[:, :],
            nb.float64[:, :],
            nb.float64[:, :],
            nb.float64[:, :, :, :],
        ),
    ],
)
def resample_vals_jit(w, x0, x1, freq, data):
    nrep, nsamp = freq.shape
    nval = w.shape[1]

    assert w.shape == x0.shape
    assert x0.shape == x1.shape
    assert w.shape[0] == nsamp
    assert data.shape[0] == nrep
    assert data.shape[1] == nval

    for irep in nb.prange(nrep):
        for isamp in range(nsamp):
            f = freq[irep, isamp]
            if f == 0:
                continue
            for k in range(nval):
                pushscalar_cov.push_val(
                    w[isamp, k] * f, x0[isamp, k], x1[isamp, k], data[irep, k, ...]
                )
