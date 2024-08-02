"""Utilities."""

from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, cast

import numpy as np

from ._missing import MISSING
from ._validate import (
    validate_mom,
    validate_mom_ndim,
    validate_not_none,
)
from .docstrings import docfiller

if TYPE_CHECKING:
    from collections.abc import (
        Hashable,
        Iterable,
        Iterator,
        Mapping,
        Sequence,
    )
    from typing import Any

    import xarray as xr
    from numpy.typing import ArrayLike, DTypeLike, NDArray

    from ._typing_compat import TypeVar
    from .typing import (
        ArrayOrder,
        ArrayOrderCF,
        AxesGUFunc,
        AxisReduce,
        AxisReduceMult,
        DimsReduce,
        DimsReduceMult,
        MissingType,
        Mom_NDim,
        MomDims,
        Moments,
        MomentsStrict,
        NDArrayAny,
        ScalarT,
    )

    T = TypeVar("T")


# * Axis normalizer
def normalize_axis_index(
    axis: int,
    ndim: int,
    mom_ndim: Mom_NDim | None = None,
    msg_prefix: str | None = None,
) -> int:
    """Interface to numpy.core.multiarray.normalize_axis_index"""
    from ._compat import (
        np_normalize_axis_index,  # pyright: ignore[reportAttributeAccessIssue]
    )

    ndim = ndim if mom_ndim is None else ndim - validate_mom_ndim(mom_ndim)
    return np_normalize_axis_index(axis, ndim, msg_prefix)  # type: ignore[no-any-return,unused-ignore]


def normalize_axis_tuple(
    axis: int | Iterable[int] | None,
    ndim: int,
    mom_ndim: Mom_NDim | None = None,
    msg_prefix: str | None = None,
    allow_duplicate: bool = False,
) -> tuple[int, ...]:
    """Interface to numpy.core.multiarray.normalize_axis_index"""
    from ._compat import (
        np_normalize_axis_tuple,  # pyright: ignore[reportAttributeAccessIssue]
    )

    ndim = ndim if mom_ndim is None else ndim - validate_mom_ndim(mom_ndim)

    if axis is None:
        return tuple(range(ndim))

    return np_normalize_axis_tuple(axis, ndim, msg_prefix, allow_duplicate)  # type: ignore[no-any-return,unused-ignore]


def positive_to_negative_index(index: int, ndim: int) -> int:
    """
    Convert positive index to negative index

    Note that this assumes that axis has been normalized via :func:`normalize_axis_index`.

    Examples
    --------
    >>> positive_to_negative_index(0, 4)
    -4
    >>> positive_to_negative_index(-1, 4)
    -1
    >>> positive_to_negative_index(2, 4)
    -2
    """
    if index < 0:
        return index
    return index - ndim


# * Array order ---------------------------------------------------------------
def arrayorder_to_arrayorder_cf(order: ArrayOrder) -> ArrayOrderCF:
    """Convert general array order to C/F/None"""
    if order is None:
        return order

    order_ = order.upper()
    if order_ in {"C", "F"}:
        return cast("ArrayOrderCF", order_)

    return None


# * peek at iterable ----------------------------------------------------------
def peek_at(iterable: Iterable[T]) -> tuple[T, Iterator[T]]:
    """Returns the first value from iterable, as well as a new iterator with
    the same content as the original iterable
    """
    gen = iter(iterable)
    peek = next(gen)
    return peek, chain([peek], gen)


@docfiller.decorate
def mom_to_mom_ndim(mom: Moments) -> Mom_NDim:
    """
    Calculate mom_ndim from mom.

    Parameters
    ----------
    {mom}

    Returns
    -------
    {mom_ndim}
    """
    mom_ndim = 1 if isinstance(mom, int) else len(mom)
    return validate_mom_ndim(mom_ndim)


@docfiller.decorate
def select_mom_ndim(*, mom: Moments | None, mom_ndim: int | None) -> Mom_NDim:
    """
    Select a mom_ndim from mom or mom_ndim

    Parameters
    ----------
    {mom}
    {mom_ndim}

    Returns
    -------
    {mom_ndim}
    """
    if mom is not None:
        mom_ndim_calc = mom_to_mom_ndim(mom)
        if mom_ndim and mom_ndim_calc != mom_ndim:
            msg = f"{mom=} is incompatible with {mom_ndim=}"
            raise ValueError(msg)
        return validate_mom_ndim(mom_ndim_calc)

    if mom_ndim is None:
        msg = "must specify mom_ndim or mom"
        raise TypeError(msg)

    return validate_mom_ndim(mom_ndim)


@docfiller.decorate
def mom_to_mom_shape(mom: int | Iterable[int]) -> MomentsStrict:
    """Convert moments to moments shape."""
    return cast("MomentsStrict", tuple(m + 1 for m in validate_mom(mom)))


@docfiller.decorate
def mom_shape_to_mom(mom_shape: int | Iterable[int]) -> MomentsStrict:
    """Convert moments shape to moments"""
    return cast("MomentsStrict", tuple(m - 1 for m in validate_mom(mom_shape)))


def select_axis_dim(
    data: xr.DataArray,
    axis: AxisReduce | MissingType = MISSING,
    dim: DimsReduce | MissingType = MISSING,
    default_axis: AxisReduce | MissingType = MISSING,
    default_dim: DimsReduce | MissingType = MISSING,
    mom_ndim: Mom_NDim | None = None,
) -> tuple[int, Hashable]:
    """Produce axis/dim from input."""
    # for now, disallow None values
    axis = validate_not_none(axis, "axis")
    dim = validate_not_none(dim, "dim")

    default_axis = validate_not_none(default_axis, "default_axis")
    default_dim = validate_not_none(default_dim, "default_dim")

    if axis is MISSING and dim is MISSING:
        if default_axis is not MISSING and default_dim is MISSING:
            axis = default_axis
        elif default_axis is MISSING and default_dim is not MISSING:
            dim = default_dim
        else:
            msg = "Must specify axis or dim, or one of default_axis or default_dim"
            raise ValueError(msg)

    elif axis is not MISSING and dim is not MISSING:
        msg = "Can only specify one of axis or dim"
        raise ValueError(msg)

    if dim is not MISSING:
        axis = data.get_axis_num(dim)
        if axis >= data.ndim - (0 if mom_ndim is None else mom_ndim):
            msg = f"Cannot select moment dimension. {axis=}, {dim=}."
            raise ValueError(msg)

    elif axis is not MISSING:
        if isinstance(axis, str):
            msg = f"Using string value for axis is deprecated.  Please use `dim` option instead.  Passed {axis} of type {type(axis)}"
            raise ValueError(msg)
        # wrap axis
        axis = normalize_axis_index(axis, data.ndim, mom_ndim)  # type: ignore[arg-type]
        dim = data.dims[axis]
    else:  # pragma: no cover
        msg = f"Unknown dim {dim} and axis {axis}"
        raise TypeError(msg)

    return axis, dim


def select_axis_dim_mult(
    data: xr.DataArray,
    axis: AxisReduceMult | MissingType = MISSING,
    dim: DimsReduceMult | MissingType = MISSING,
    default_axis: AxisReduceMult | MissingType = MISSING,
    default_dim: DimsReduceMult | MissingType = MISSING,
    mom_ndim: Mom_NDim | None = None,
) -> tuple[tuple[int, ...], tuple[Hashable, ...]]:
    """
    Produce axis/dim tuples from input.

    This is like `select_axis_dim`, but allows multiple values in axis/dim.
    """
    # Allow None, which implies choosing all dimensions...
    if axis is MISSING and dim is MISSING:
        if default_axis is not MISSING and default_dim is MISSING:
            axis = default_axis
        elif default_axis is MISSING and default_dim is not MISSING:
            dim = default_dim
        else:
            msg = "Must specify axis or dim, or one of default_axis or default_dim"
            raise ValueError(msg)

    elif axis is not MISSING and dim is not MISSING:
        msg = "Can only specify one of axis or dim"
        raise ValueError(msg)

    ndim = data.ndim - (0 if mom_ndim is None else mom_ndim)
    dim_: tuple[Hashable, ...]
    axis_: tuple[int, ...]

    if dim is not MISSING:
        dim_ = (
            data.dims[:ndim]
            if dim is None
            else (dim,)
            if isinstance(dim, str)
            else tuple(dim)  # type: ignore[arg-type]
        )

        axis_ = data.get_axis_num(dim_)
        if any(a >= ndim for a in axis_):
            msg = f"Cannot select moment dimension. {axis_=}, {dim_=}."
            raise ValueError(msg)

    elif axis is not MISSING:
        axis_ = normalize_axis_tuple(axis, data.ndim, mom_ndim)
        dim_ = tuple(data.dims[a] for a in axis_)

    else:  # pragma: no cover
        msg = f"Unknown dim {dim} and axis {axis}"
        raise TypeError(msg)

    return axis_, dim_


def get_axes_from_values(*args: NDArrayAny, axis_neg: int) -> AxesGUFunc:
    """Get reduction axes for arrays..."""
    return [(-1,) if a.ndim == 1 else (axis_neg,) for a in args]


def get_out_from_values(
    *args: NDArray[ScalarT],
    mom: MomentsStrict,
    axis_neg: int,
    axis_new_size: int | None = None,
) -> NDArray[ScalarT]:
    """Pass in axis if this is a reduction and will be removing axis_neg"""
    val_shape: tuple[int, ...] = np.broadcast_shapes(
        args[0].shape, *(a.shape for a in args[1:] if a.ndim > 1)
    )

    # need to normalize
    axis = normalize_axis_index(axis_neg, len(val_shape))
    if axis_new_size is None:
        val_shape = (*val_shape[:axis], *val_shape[axis + 1 :])
    else:
        val_shape = (*val_shape[:axis], axis_new_size, *val_shape[axis + 1 :])

    out_shape = (*val_shape, *mom_to_mom_shape(mom))
    return np.zeros(out_shape, dtype=args[0].dtype)


def raise_if_wrong_shape(
    array: NDArrayAny, shape: tuple[int, ...], name: str | None = None
) -> None:
    """Raise error if array.shape != shape"""
    if array.shape != shape:
        name = "out" if name is None else name
        msg = f"{name}.shape={array.shape=} != required shape {shape}"
        raise ValueError(msg)


_ALLOWED_FLOAT_DTYPES = {np.dtype(np.float32), np.dtype(np.float64)}


def select_dtype(
    x: xr.DataArray | ArrayLike,
    out: NDArrayAny | xr.DataArray | None,
    dtype: DTypeLike,
) -> np.dtype[np.float32] | np.dtype[np.float64]:  # DTypeLikeArg[Any]:
    """Select a dtype from, in order, out, dtype, or passed array."""
    if out is not None:
        dtype = out.dtype
    elif dtype is not None:
        dtype = np.dtype(dtype)
    else:
        dtype = getattr(x, "dtype", np.dtype(np.float64))

    if dtype in _ALLOWED_FLOAT_DTYPES:
        return dtype  # type: ignore[return-value]

    msg = f"{dtype=} not supported.  dtype must be conformable to float32 or float64."
    raise ValueError(msg)


def optional_keepdims(
    x: NDArray[ScalarT],
    *,
    axis: int | Sequence[int],
    keepdims: bool = False,
) -> NDArray[ScalarT]:
    if keepdims:
        return np.expand_dims(x, axis)
    return x


# new style preparation for reduction....
_MOM_AXES_TUPLE = {1: (-1,), 2: (-2, -1)}


def axes_data_reduction(
    *inner: int | tuple[int, ...],
    mom_ndim: Mom_NDim,
    axis: int,
    out_has_axis: bool = False,
) -> AxesGUFunc:
    """
    axes for reducing data along axis

    if ``out_has_axis == True``, then treat like resample,
    so output will still have ``axis`` with new size in output.

    It is assumed that `axis` is validated against a moments array,
    (i.e., negative values should be ``< -mom_ndim``)

    Can also pass in "inner" dimensions (elements 1:-1 of output)
    """
    mom_axes = _MOM_AXES_TUPLE[mom_ndim]
    data_axes = (axis, *mom_axes)
    out_axes = data_axes if out_has_axis else mom_axes

    return [
        data_axes,
        *((x,) if isinstance(x, int) else x for x in inner),
        out_axes,
    ]


# def optional_move_end_to_axis(
#     out: NDArray[ScalarT],
#     *,
#     mom_ndim: Mom_NDim,
#     axis: int,
# ) -> NDArray[ScalarT]:
#     """
#     Move 'last' axis back to original position

#     Note that this assumes axis is negative (relative to end of array), and relative to `mom_dim`.
#     """
#     if axis != -1:
#         np.moveaxis(out, -(mom_ndim + 1), axis - mom_ndim)  # noqa: ERA001
#     return out  # noqa: ERA001


# * Xarray utilities ----------------------------------------------------------
def move_mom_dims_to_end(
    x: xr.DataArray, mom_dims: MomDims, mom_ndim: Mom_NDim | None = None
) -> xr.DataArray:
    """Move moment dimensions to end"""
    if mom_dims is not None:
        mom_dims = (mom_dims,) if isinstance(mom_dims, str) else tuple(mom_dims)  # type: ignore[arg-type]

        if mom_ndim is not None and len(mom_dims) != mom_ndim:
            msg = f"len(mom_dims)={len(mom_dims)} not equal to mom_ndim={mom_ndim}"
            raise ValueError(msg)

        x = x.transpose(..., *mom_dims)  # pyright: ignore[reportUnknownArgumentType]

    return x


def replace_coords_from_isel(
    da_original: xr.DataArray,
    da_selected: xr.DataArray,
    indexers: Mapping[Any, Any] | None = None,
    drop: bool = False,
    **indexers_kwargs: Any,
) -> xr.DataArray:
    """
    Replace coords in da_selected with coords from coords from da_original.isel(...).

    This assumes that `da_selected` is the result of soe operation, and that indexeding
    ``da_original`` will give the correct coordinates/indexed.

    Useful for adding back coordinates to reduced object.
    """
    from xarray.core.indexes import (
        isel_indexes,  # pyright: ignore[reportUnknownVariableType]
    )
    from xarray.core.indexing import is_fancy_indexer

    # Would prefer to import from actual source by old xarray error.
    from xarray.core.utils import either_dict_or_kwargs  # type: ignore[attr-defined]

    indexers = either_dict_or_kwargs(indexers, indexers_kwargs, "isel")
    if any(is_fancy_indexer(idx) for idx in indexers.values()):  # pragma: no cover
        msg = "no fancy indexers for this"
        raise ValueError(msg)

    indexes, index_variables = isel_indexes(da_original.xindexes, indexers)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    coords = {}
    for coord_name, coord_value in da_original._coords.items():  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        if coord_name in index_variables:
            coord_value = index_variables[coord_name]  # noqa: PLW2901
        else:
            coord_indexers = {
                k: v for k, v in indexers.items() if k in coord_value.dims
            }
            if coord_indexers:
                coord_value = coord_value.isel(coord_indexers)  # noqa: PLW2901
                if drop and coord_value.ndim == 0:
                    continue
        coords[coord_name] = coord_value

    return da_selected._replace(coords=coords, indexes=indexes)  # pyright: ignore[reportUnknownMemberType, reportPrivateUsage]
