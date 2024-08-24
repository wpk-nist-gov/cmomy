"""Validators"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import xarray as xr

from .docstrings import docfiller
from .missing import MISSING

if TYPE_CHECKING:
    from collections.abc import (
        Hashable,
        Iterable,
        Sequence,
    )
    from typing import Any

    from numpy.typing import DTypeLike

    from .typing import (
        AxisReduce,
        AxisReduceMult,
        MissingType,
        Mom_NDim,
        MomDimsStrict,
        Moments,
        MomentsStrict,
    )
    from .typing_compat import TypeGuard, TypeVar

    T = TypeVar("T")


# * TypeGuards ----------------------------------------------------------------
def is_dataarray(x: Any) -> TypeGuard[xr.DataArray]:
    """Typeguard dataarray."""
    return isinstance(x, xr.DataArray)


def is_dataset(x: Any) -> TypeGuard[xr.Dataset]:
    """Typeguard dataset"""
    return isinstance(x, xr.Dataset)


def is_xarray(x: Any) -> TypeGuard[xr.Dataset | xr.DataArray]:
    """Typeguard xarray object"""
    return isinstance(x, (xr.DataArray, xr.Dataset))


def are_same_type(*args: Any) -> bool:
    """Check if all args are the same type."""
    type0: Any = type(args[0])
    return any(type0 is not type(a) for a in args[1:])


# * Moment validation ---------------------------------------------------------
def is_mom_ndim(mom_ndim: int | None) -> TypeGuard[Mom_NDim]:
    """Validate mom_ndim."""
    return mom_ndim in {1, 2}


def is_mom_tuple(mom: tuple[int, ...]) -> TypeGuard[MomentsStrict]:
    """Validate moment tuple"""
    return len(mom) in {1, 2} and all(m > 0 for m in mom)


def validate_mom_ndim(mom_ndim: int | None) -> Mom_NDim:
    """Raise error if mom_ndim invalid."""
    if is_mom_ndim(mom_ndim):
        return mom_ndim

    msg = f"{mom_ndim=} must be either 1 or 2"
    raise ValueError(msg)


def validate_mom(mom: int | Iterable[int]) -> MomentsStrict:
    """
    Convert to MomentsStrict.

    Raise ValueError mom invalid.

    Integers to length 1 tuple
    """
    if isinstance(mom, int):
        mom = (mom,)
    elif not isinstance(mom, tuple):
        mom = tuple(mom)

    if is_mom_tuple(mom):
        return mom

    msg = f"{mom=} must be an integer, or tuple of length 1 or 2, with positive values."
    raise ValueError(msg)


@docfiller.decorate
def validate_mom_and_mom_ndim(
    *,
    mom: Moments | None = None,
    mom_ndim: int | None = None,
    shape: tuple[int, ...] | None = None,
) -> tuple[MomentsStrict, Mom_NDim]:
    """
    Validate mom and mom_ndim to optional shape.

    Parameters
    ----------
    {mom}
    {mom_ndim}
    shape: target shape, optional
        This can be used to infer the ``mom`` from ``shape[-mom_ndim:]``

    Returns
    -------
    mom : tuple of int
        Moments tuple.
    mom_ndim: int
        moment ndim.

    Examples
    --------
    >>> validate_mom_and_mom_ndim(mom=1)
    ((1,), 1)
    >>> validate_mom_and_mom_ndim(mom=(2, 2))
    ((2, 2), 2)
    >>> validate_mom_and_mom_ndim(mom_ndim=1, shape=(3, 3))
    ((2,), 1)
    """
    if mom is not None and mom_ndim is not None:
        mom_ndim = validate_mom_ndim(mom_ndim)
        mom = validate_mom(mom)
        if len(mom) != mom_ndim:
            msg = f"{len(mom)=} != {mom_ndim=}"
            raise ValueError(msg)
        return mom, mom_ndim

    if mom is None and mom_ndim is not None and shape is not None:
        mom_ndim = validate_mom_ndim(mom_ndim)
        if len(shape) < mom_ndim:
            raise ValueError
        mom = validate_mom(tuple(x - 1 for x in shape[-mom_ndim:]))
        return mom, mom_ndim

    if mom is not None and mom_ndim is None:
        mom = validate_mom(mom)
        mom_ndim = validate_mom_ndim(len(mom))
        return mom, mom_ndim

    msg = "Must specify either mom, mom and mom_ndim, or shape and mom_ndim"
    raise ValueError(msg)


# * Validate type -------------------------------------------------------------
@docfiller.decorate
def validate_floating_dtype(
    dtype: DTypeLike,
    name: Hashable = "array",
) -> None | np.dtype[np.float32] | np.dtype[np.float64]:
    """
    Validate that dtype is conformable float32 or float64.

    Parameters
    ----------
    {dtype}

    Returns
    -------
    `numpy.dtype` object or None
        Note that if ``dtype == None``, ``None`` will be returned.
        Otherwise, will return ``np.dtype(dtype)``.


    """
    if dtype is None:
        # defaults to np.float64, but can have special properties
        # e.g., to np.asarray(..., dtype=None) means infer...
        return dtype

    dtype = np.dtype(dtype)
    if dtype.type in {np.float32, np.float64}:
        return dtype  # type: ignore[return-value]

    msg = f"{dtype=} not supported for {name}.  dtype must be conformable to float32 or float64."
    raise ValueError(msg)


def validate_not_none(x: T | None, name: str = "value") -> T:
    """
    Raise if value is None

    Use for now to catch any cases where `axis=None` or `dim=None`.
    These values are reserved for total reduction...
    """
    if x is None:
        msg = f"{name}={x} is not supported"
        raise TypeError(msg)
    return x


# * Validate Axis -------------------------------------------------------------
def validate_axis(axis: AxisReduce | MissingType) -> int:
    """
    Validate that axis is an integer.

    In the future, will allow axis to be None also.
    """
    if axis is None or axis is MISSING:
        msg = f"Must specify axis. Received {axis=}."
        raise TypeError(msg)
    return axis


def validate_axis_mult(axis: AxisReduceMult | MissingType) -> AxisReduceMult:
    """Validate that axis is specified."""
    if axis is MISSING:
        msg = f"Must specify axis. Received {axis=}."
        raise TypeError(msg)
    return axis


# * DataArray -----------------------------------------------------------------
def validate_mom_dims(
    mom_dims: Hashable | Sequence[Hashable] | None,
    mom_ndim: Mom_NDim,
    out: Any = None,
) -> MomDimsStrict:
    """Validate mom_dims to correct form."""
    if mom_dims is None:
        if is_dataset(out):
            # select first array in dataset
            out = out[next(iter(out))]

        if is_dataarray(out):
            return cast("MomDimsStrict", out.dims[-mom_ndim:])

        if mom_ndim == 1:
            return ("mom_0",)
        return ("mom_0", "mom_1")

    validated: tuple[Hashable, ...]
    if isinstance(mom_dims, str):
        validated = (mom_dims,)
    elif isinstance(mom_dims, (tuple, list)):
        validated = tuple(mom_dims)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
    else:
        msg = f"Unknown {type(mom_dims)=}.  Expected str or Sequence[str]"
        raise TypeError(msg)

    if len(validated) != mom_ndim:  # pyright: ignore[reportUnknownArgumentType]
        msg = f"mom_dims={validated} inconsistent with {mom_ndim=}"
        raise ValueError(msg)
    return cast("MomDimsStrict", validated)
