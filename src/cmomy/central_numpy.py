"""
Central moments/comoments routines from :class:`np.ndarray` objects
-------------------------------------------------------------------.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, overload

import numpy as np
import pandas as pd  # noqa: F401  # pyright: ignore[reportUnusedImport]
import xarray as xr

# pandas needed for autdoc typehints
from numpy.typing import NDArray

from cmomy.utils import validate_mom_and_mom_ndim

from .central_abc import CentralMomentsABC
from .docstrings import docfiller_central as docfiller

if TYPE_CHECKING:
    from typing import Any

    from numpy.typing import ArrayLike, DTypeLike

    from ._typing_compat import Self
    from .central_dataarray import xCentralMoments
    from .typing import (
        ArrayLikeArg,
        ArrayOrder,
        ArrayOrderCF,
        ArrayOrderCFA,
        DataCasting,
        DTypeLikeArg,
        Groups,
        Mom_NDim,
        MomDims,
        Moments,
        NDArrayAny,
        NDArrayInt,
        T_Float2,
        XArrayAttrsType,
        XArrayCoordsType,
        XArrayDimsType,
        XArrayIndexesType,
        XArrayNameType,
    )

from .typing import (
    T_Float,
)

# from ._typing_compat import TypeVar


docfiller_abc = docfiller.factory_from_parent(CentralMomentsABC)
docfiller_inherit_abc = docfiller.factory_inherit_from_parent(CentralMomentsABC)


# * CentralMoments ------------------------------------------------------------
@docfiller(CentralMomentsABC)  # noqa: PLR0904
class CentralMoments(CentralMomentsABC[T_Float, NDArray[T_Float]], Generic[T_Float]):  # type: ignore[type-var] # noqa: D101
    # TODO(wpk):  I think something like this would solve some of my typing issues.
    # see https://mypy.readthedocs.io/en/stable/more_types.html#precise-typing-of-alternative-constructors
    # But pyright isn't going to support it (see https://github.com/microsoft/pyright/issues/3497)
    #
    # _CentralT = TypeVar("_CentralT", bound="CentralMoments[T_Float]")

    @overload
    def __init__(
        self,
        data: ArrayLikeArg[T_Float],
        *,
        mom_ndim: Mom_NDim = ...,
        copy: bool = ...,
        order: ArrayOrder = ...,
        dtype: None = ...,
        fastpath: bool = ...,
    ) -> None: ...
    @overload
    def __init__(
        self,
        data: Any,
        *,
        mom_ndim: Mom_NDim = ...,
        copy: bool = ...,
        order: ArrayOrder = ...,
        dtype: DTypeLikeArg[T_Float],
        fastpath: bool = ...,
    ) -> None: ...
    @overload
    def __init__(
        self,
        data: Any,
        *,
        mom_ndim: Mom_NDim = ...,
        copy: bool = ...,
        order: ArrayOrder = ...,
        dtype: DTypeLike = ...,
        fastpath: bool = ...,
    ) -> None: ...

    def __init__(
        self,
        data: ArrayLike,
        *,
        mom_ndim: Mom_NDim = 1,
        copy: bool = False,
        order: ArrayOrder = None,
        dtype: DTypeLike = None,
        fastpath: bool = False,
    ) -> None:
        if fastpath:
            if not isinstance(data, np.ndarray):
                msg = "Must pass ndarray with fastpath"
                raise TypeError(msg)
            self._cache = {}
            self._data = data
            self._mom_ndim = mom_ndim
        else:
            super().__init__(
                data=np.array(data, dtype=dtype, order=order, copy=copy),
                mom_ndim=mom_ndim,
            )

    def set_values(self, values: NDArray[T_Float]) -> None:
        if not isinstance(values, np.ndarray):
            msg = f"Must pass numpy.ndarray as data.  Not {type(values)=}"
            raise TypeError(msg)
        self._data = values

    def to_values(self) -> NDArray[T_Float]:
        return self._data

    # * top level creation/copy/new -----------------------------------------------
    @overload
    def new_like(
        self,
        data: NDArray[T_Float2],
        *,
        copy: bool = ...,
        order: ArrayOrder = ...,
        verify: bool = ...,
        dtype: None = ...,
    ) -> CentralMoments[T_Float2]: ...
    @overload
    def new_like(
        self,
        data: Any = ...,
        *,
        copy: bool = ...,
        order: ArrayOrder = ...,
        verify: bool = ...,
        dtype: DTypeLikeArg[T_Float2],
    ) -> CentralMoments[T_Float2]: ...
    @overload
    def new_like(
        self,
        data: None = ...,
        *,
        copy: bool = ...,
        order: ArrayOrder = ...,
        verify: bool = ...,
        dtype: None = ...,
    ) -> Self: ...
    @overload
    def new_like(
        self,
        data: Any = ...,
        *,
        copy: bool = ...,
        order: ArrayOrder = ...,
        verify: bool = ...,
        dtype: Any = ...,
    ) -> CentralMoments[Any]: ...

    @docfiller_abc()
    def new_like(
        self,
        data: NDArrayAny | None = None,
        *,
        copy: bool = False,
        order: ArrayOrder = None,
        verify: bool = False,
        dtype: DTypeLike = None,
    ) -> CentralMoments[Any]:
        """
        Examples
        --------
        >>> from cmomy.random import default_rng
        >>> rng = default_rng(0)
        >>> da = CentralMoments.from_vals(rng.random(10), mom=3, axis=0)
        >>> da
        <CentralMoments(val_shape=(), mom=(3,))>
        array([10.    ,  0.5505,  0.1014, -0.0178])

        >>> da2 = da.new_like().zero()
        >>> da2
        <CentralMoments(val_shape=(), mom=(3,))>
        array([0., 0., 0., 0.])

        >>> da
        <CentralMoments(val_shape=(), mom=(3,))>
        array([10.    ,  0.5505,  0.1014, -0.0178])

        """
        if data is None:
            data = np.zeros(
                self.shape,
                order=order if order in {"C", "F"} else None,  # type: ignore[arg-type]
                dtype=dtype or self.dtype,  # type: ignore[arg-type]
            )
            copy = verify = False

        if verify and data.shape != self.shape:
            msg = f"{data.shape=} != {self.shape=}"
            raise ValueError(msg)
        if data.shape[-self.mom_ndim :] != self.mom_shape:
            # at a minimum, verify that mom_shape is unchanged.
            msg = f"{data.shape=} has wrong mom_shape={self.mom_shape}"
            raise ValueError(msg)

        return type(self)(
            data=data,
            copy=copy,
            mom_ndim=self.mom_ndim,
            order=order,
            dtype=dtype,
        )

    @overload
    def astype(
        self,
        dtype: DTypeLikeArg[T_Float2],
        *,
        order: ArrayOrder = None,
        casting: DataCasting = None,
        subok: bool | None = None,
        copy: bool = False,
    ) -> CentralMoments[T_Float2]: ...
    @overload
    def astype(
        self,
        dtype: None,
        *,
        order: ArrayOrder = None,
        casting: DataCasting = None,
        subok: bool | None = None,
        copy: bool = False,
    ) -> CentralMoments[np.float64]: ...
    @overload
    def astype(
        self,
        dtype: DTypeLike,
        *,
        order: ArrayOrder = None,
        casting: DataCasting = None,
        subok: bool | None = None,
        copy: bool = False,
    ) -> CentralMoments[Any]: ...

    @docfiller_abc()
    def astype(
        self,
        dtype: DTypeLike,
        *,
        order: ArrayOrder = None,
        casting: DataCasting = None,
        subok: bool | None = None,
        copy: bool = False,
    ) -> CentralMoments[Any]:
        return super().astype(
            dtype=dtype, order=order, casting=casting, subok=subok, copy=copy
        )

    # * To/from xarray ------------------------------------------------------------
    @docfiller.decorate
    def to_dataarray(  # noqa: PLR0912
        self,
        *,
        dims: XArrayDimsType = None,
        attrs: XArrayAttrsType = None,
        coords: XArrayCoordsType = None,
        name: XArrayNameType = None,
        indexes: XArrayIndexesType = None,  # noqa: ARG002
        mom_dims: MomDims | None = None,
        template: xr.DataArray | None = None,
        copy: bool = False,
    ) -> xr.DataArray:
        """
        Create a :class:`xarray.DataArray` representation of underlying data.

        Parameters
        ----------
        {xr_params}
        {copy}

        Returns
        -------
        output : DataArray


        Examples
        --------
        >>> from cmomy.random import default_rng
        >>> rng = default_rng(0)
        >>> da = CentralMoments.from_vals(rng.random((10, 1, 2)), axis=0, mom=2)
        >>> da
        <CentralMoments(val_shape=(1, 2), mom=(2,))>
        array([[[10.    ,  0.6207,  0.0647],
                [10.    ,  0.404 ,  0.1185]]])

        Default constructor

        >>> da.to_dataarray()
        <xarray.DataArray (dim_0: 1, dim_1: 2, mom_0: 3)> Size: 48B
        array([[[10.    ,  0.6207,  0.0647],
                [10.    ,  0.404 ,  0.1185]]])
        Dimensions without coordinates: dim_0, dim_1, mom_0

        Setting attributes

        >>> da.to_dataarray()
        <xarray.DataArray (dim_0: 1, dim_1: 2, mom_0: 3)> Size: 48B
        array([[[10.    ,  0.6207,  0.0647],
                [10.    ,  0.404 ,  0.1185]]])
        Dimensions without coordinates: dim_0, dim_1, mom_0
        >>> da
        <CentralMoments(val_shape=(1, 2), mom=(2,))>
        array([[[10.    ,  0.6207,  0.0647],
                [10.    ,  0.404 ,  0.1185]]])

        """
        data = self.data
        if copy:
            data = data.copy()

        if template is not None:
            out = template.copy(data=data)
        else:
            if dims is None:
                dims = tuple(f"dim_{i}" for i in range(self.val_ndim))
            elif isinstance(dims, str):
                dims = (dims,)
            else:
                # try to convert to tuple
                dims = tuple(dims)  # type: ignore[arg-type]

            if len(dims) == self.ndim:
                dims_output = dims

            elif len(dims) == self.val_ndim:
                if mom_dims is None:
                    mom_dims = tuple(f"mom_{i}" for i in range(self.mom_ndim))
                elif isinstance(mom_dims, str):
                    mom_dims = (mom_dims,)
                else:
                    # try to convert to tuple
                    mom_dims = tuple(mom_dims)  # type: ignore[arg-type]

                if len(mom_dims) != self.mom_ndim:
                    msg = f"{mom_dims=} != {self.mom_ndim=}"
                    raise ValueError(msg)

                dims_output = dims + mom_dims

            else:
                msg = f"Problem with {dims}, {mom_dims}.  Total length should be {self.ndim}"
                raise ValueError(msg)
            out = xr.DataArray(
                data, dims=dims_output, coords=coords, attrs=attrs, name=name
            )

        return out

    @docfiller.decorate
    def to_xcentralmoments(
        self,
        *,
        dims: XArrayDimsType = None,
        attrs: XArrayAttrsType = None,
        coords: XArrayCoordsType = None,
        name: XArrayNameType = None,
        indexes: XArrayIndexesType = None,
        mom_dims: MomDims | None = None,
        template: xr.DataArray | None = None,
        copy: bool = False,
    ) -> xCentralMoments[T_Float]:
        """
        Create an :class:`xarray.DataArray` representation of underlying data.

        Parameters
        ----------
        {xr_params}
        {copy}

        Returns
        -------
        output : xCentralMoments

        See Also
        --------
        to_dataarray

        Examples
        --------
        >>> from cmomy.random import default_rng
        >>> rng = default_rng(0)
        >>> da = CentralMoments.from_vals(rng.random((10, 1, 2)), axis=0, mom=2)
        >>> da
        <CentralMoments(val_shape=(1, 2), mom=(2,))>
        array([[[10.    ,  0.6207,  0.0647],
                [10.    ,  0.404 ,  0.1185]]])

        Default constructor

        >>> da.to_xcentralmoments()
        <xCentralMoments(val_shape=(1, 2), mom=(2,))>
        <xarray.DataArray (dim_0: 1, dim_1: 2, mom_0: 3)> Size: 48B
        array([[[10.    ,  0.6207,  0.0647],
                [10.    ,  0.404 ,  0.1185]]])
        Dimensions without coordinates: dim_0, dim_1, mom_0

        Setting attributes

        >>> da.to_xcentralmoments()
        <xCentralMoments(val_shape=(1, 2), mom=(2,))>
        <xarray.DataArray (dim_0: 1, dim_1: 2, mom_0: 3)> Size: 48B
        array([[[10.    ,  0.6207,  0.0647],
                [10.    ,  0.404 ,  0.1185]]])
        Dimensions without coordinates: dim_0, dim_1, mom_0
        >>> da
        <CentralMoments(val_shape=(1, 2), mom=(2,))>
        array([[[10.    ,  0.6207,  0.0647],
                [10.    ,  0.404 ,  0.1185]]])

        """
        from .central_dataarray import xCentralMoments

        data = self.to_dataarray(
            dims=dims,
            attrs=attrs,
            coords=coords,
            name=name,
            indexes=indexes,
            mom_dims=mom_dims,
            template=template,
            copy=copy,
        )
        return xCentralMoments(data=data, mom_ndim=self.mom_ndim)  # , fastpath=True)

    def to_x(
        self,
        *,
        dims: XArrayDimsType = None,
        attrs: XArrayAttrsType = None,
        coords: XArrayCoordsType = None,
        name: XArrayNameType = None,
        indexes: XArrayIndexesType = None,
        mom_dims: MomDims | None = None,
        template: xr.DataArray | None = None,
        copy: bool = False,
    ) -> xCentralMoments[T_Float]:
        """Alias to :meth:`to_xcentralmoments`."""
        return self.to_xcentralmoments(
            dims=dims,
            attrs=attrs,
            coords=coords,
            name=name,
            indexes=indexes,
            mom_dims=mom_dims,
            template=template,
            copy=copy,
        )

    # * pushing routines ----------------------------------------------------------
    @docfiller_inherit_abc()
    def push_data(
        self,
        data: ArrayLike,
        *,
        order: ArrayOrder = None,
        parallel: bool | None = False,
    ) -> Self:
        """
        Examples
        --------
        >>> import cmomy
        >>> rng = cmomy.random.default_rng(0)
        >>> xs = rng.random((2, 10))
        >>> datas = [cmomy.reduce_vals(x, mom=2, axis=0) for x in xs]
        >>> da = CentralMoments(datas[0], mom_ndim=1)
        >>> da
        <CentralMoments(val_shape=(), mom=(2,))>
        array([10.    ,  0.5505,  0.1014])


        >>> da.push_data(datas[1])
        <CentralMoments(val_shape=(), mom=(2,))>
        array([20.    ,  0.5124,  0.1033])


        Which is equivalent to

        >>> CentralMoments.from_vals(xs.reshape(-1), mom=2)
        <CentralMoments(val_shape=(), mom=(2,))>
        array([20.    ,  0.5124,  0.1033])

        """
        return self._push_data_numpy(data, order=order, parallel=parallel)

    @docfiller_inherit_abc()
    def push_datas(
        self,
        datas: ArrayLike,
        *,
        axis: int | None = None,
        order: ArrayOrder = None,
        parallel: bool | None = None,
    ) -> Self:
        """
        Examples
        --------
        >>> import cmomy
        >>> rng = cmomy.random.default_rng(0)
        >>> xs = rng.random((2, 10))
        >>> datas = cmomy.reduce_vals(xs, axis=1, mom=2)
        >>> da = CentralMoments.zeros(mom=2)
        >>> da.push_datas(datas, axis=0)
        <CentralMoments(val_shape=(), mom=(2,))>
        array([20.    ,  0.5124,  0.1033])


        Which is equivalent to

        >>> CentralMoments.from_vals(xs.reshape(-1), mom=2, axis=0)
        <CentralMoments(val_shape=(), mom=(2,))>
        array([20.    ,  0.5124,  0.1033])
        """
        return self._push_datas_numpy(datas, axis=axis, order=order, parallel=parallel)

    @docfiller_inherit_abc()
    def push_val(
        self,
        x: ArrayLike,
        *y: ArrayLike,
        weight: ArrayLike | None = None,
        order: ArrayOrder = None,
        parallel: bool | None = False,
    ) -> Self:
        """
        Examples
        --------
        >>> import cmomy
        >>> rng = cmomy.random.default_rng(0)
        >>> x = rng.random((10, 2))
        >>> y = rng.random(10)
        >>> w = rng.random(10)

        >>> da = CentralMoments.zeros(val_shape=(2,), mom=(2, 2))
        >>> for xx, yy, ww in zip(x, y, w):
        ...     _ = da.push_val(xx, yy, weight=ww)

        >>> da
        <CentralMoments(val_shape=(2,), mom=(2, 2))>
        array([[[ 5.4367e+00,  6.0656e-01,  9.9896e-02],
                [ 6.4741e-01,  3.3791e-02, -5.1117e-03],
                [ 5.0888e-02, -1.0060e-02,  7.0290e-03]],
        <BLANKLINE>
               [[ 5.4367e+00,  6.0656e-01,  9.9896e-02],
                [ 3.9793e-01,  6.3224e-03, -2.2669e-02],
                [ 9.3979e-02,  9.9433e-04,  6.5765e-03]]])


        Which is the same as

        >>> CentralMoments.from_vals(x, y, weight=w, mom=(2, 2), axis=0)
        <CentralMoments(val_shape=(2,), mom=(2, 2))>
        array([[[ 5.4367e+00,  6.0656e-01,  9.9896e-02],
                [ 6.4741e-01,  3.3791e-02, -5.1117e-03],
                [ 5.0888e-02, -1.0060e-02,  7.0290e-03]],
        <BLANKLINE>
               [[ 5.4367e+00,  6.0656e-01,  9.9896e-02],
                [ 3.9793e-01,  6.3224e-03, -2.2669e-02],
                [ 9.3979e-02,  9.9433e-04,  6.5765e-03]]])

        """
        return self._push_val_numpy(
            x, *y, weight=weight, order=order, parallel=parallel
        )

    @docfiller_inherit_abc()
    def push_vals(
        self,
        x: ArrayLike,
        *y: ArrayLike,
        weight: ArrayLike | None = None,
        axis: int | None = None,
        order: ArrayOrder = None,
        parallel: bool | None = None,
    ) -> Self:
        """
        Examples
        --------
        >>> import cmomy
        >>> rng = cmomy.random.default_rng(0)
        >>> x = rng.random((10, 2))
        >>> y = rng.random(10)
        >>> w = rng.random(10)

        >>> da = CentralMoments.zeros(val_shape=(2,), mom=(2, 2))
        >>> da.push_vals(x, y, weight=w, axis=0)
        <CentralMoments(val_shape=(2,), mom=(2, 2))>
        array([[[ 5.4367e+00,  6.0656e-01,  9.9896e-02],
                [ 6.4741e-01,  3.3791e-02, -5.1117e-03],
                [ 5.0888e-02, -1.0060e-02,  7.0290e-03]],
        <BLANKLINE>
               [[ 5.4367e+00,  6.0656e-01,  9.9896e-02],
                [ 3.9793e-01,  6.3224e-03, -2.2669e-02],
                [ 9.3979e-02,  9.9433e-04,  6.5765e-03]]])


        Which is the same as

        >>> CentralMoments.from_vals(x, y, weight=w, mom=(2, 2), axis=0)
        <CentralMoments(val_shape=(2,), mom=(2, 2))>
        array([[[ 5.4367e+00,  6.0656e-01,  9.9896e-02],
                [ 6.4741e-01,  3.3791e-02, -5.1117e-03],
                [ 5.0888e-02, -1.0060e-02,  7.0290e-03]],
        <BLANKLINE>
               [[ 5.4367e+00,  6.0656e-01,  9.9896e-02],
                [ 3.9793e-01,  6.3224e-03, -2.2669e-02],
                [ 9.3979e-02,  9.9433e-04,  6.5765e-03]]])

        """
        return self._push_vals_numpy(
            x, *y, weight=weight, axis=axis, order=order, parallel=parallel
        )

    # ** Reduction ----------------------------------------------------------------
    @docfiller_inherit_abc()
    def resample_and_reduce(
        self,
        *,
        freq: NDArrayInt,
        axis: int | None = None,
        parallel: bool | None = None,
        order: ArrayOrder = None,
    ) -> Self:
        self._raise_if_scalar()
        from .resample import resample_data

        axis = self._set_default_axis(axis)

        data: NDArray[T_Float] = resample_data(
            self._data,
            freq=freq,
            mom_ndim=self._mom_ndim,
            axis=axis,
            order=order,
            parallel=parallel,
        )
        return type(self)(data=data, mom_ndim=self.mom_ndim)

    @docfiller_inherit_abc()
    def reduce(
        self,
        *,
        axis: int | None = None,
        by: Groups | None = None,
        order: ArrayOrder = None,
        parallel: bool | None = None,
    ) -> Self:
        self._raise_if_scalar()
        if by is None:
            from .reduction import reduce_data

            data = reduce_data(
                self._data,
                mom_ndim=self._mom_ndim,
                axis=self._set_default_axis(axis),
                order=order,
                parallel=parallel,
                dtype=self.dtype,
            )
        else:
            from .reduction import reduce_data_grouped

            data = reduce_data_grouped(
                self._data,
                mom_ndim=self._mom_ndim,
                by=by,
                axis=self._set_default_axis(axis),
                order=order,
                parallel=parallel,
                dtype=self.dtype,
            )
        return type(self)(data=data, mom_ndim=self._mom_ndim, fastpath=True)

    @docfiller.decorate
    def resample(
        self,
        indices: NDArrayInt,
        *,
        axis: int | None = None,
        last: bool = True,
        order: ArrayOrder = None,
    ) -> CentralMoments[T_Float]:
        """
        Create a new object sampled from index.

        Parameters
        ----------
        {indices}
        {axis_data_and_dim}
        last : bool, default=True
            If ``True``, and axis != -1, move the axis to last position before moments.
            This makes results similar to resample and reduce
            If `last` False, then resampled array can have odd shape
        {order}

        Returns
        -------
        output : object
            Instance of calling class. The new object will have shape
            ``(..., shape[axis-1], nrep, nsamp, shape[axis+1], ...)``,
            (if ``last=False``) or shape
            ``(..., shape[axis-1], shape[axis+1], ..., nrep, nsamp, mom_0, ...)``
            (if ``last=True``),
            where ``shape=self.data`` and ``nrep, nsamp = indices.shape``.


        """
        self._raise_if_scalar()
        axis = self._set_default_axis(axis)

        data = self.data
        last_dim = self.val_ndim - 1
        if last and axis != last_dim:
            data = np.moveaxis(data, axis, last_dim)
            axis = last_dim

        out = np.take(data, indices, axis=axis)  # pyright: ignore[reportUnknownMemberType]

        return type(self)(
            data=out,
            mom_ndim=self.mom_ndim,
            copy=False,  # pyright: ignore[reportUnknownMemberType]
            order=order,
        )

    @docfiller.decorate
    def block(
        self,
        block_size: int | None = None,
        axis: int | None = None,
        order: ArrayOrder = None,
        parallel: bool | None = None,
        # **kwargs: Any,
    ) -> Self:
        """
        Block average reduction.

        Parameters
        ----------
        block_size : int
            number of consecutive records to combine
        {axis}

        Returns
        -------
        output : object
            Block averaged data of shape
            ``(..., shape[axis-1],shape[axis+1], ..., nblock, mom_0, ...)``
            Where ``shape=self.shape``.  That is, the blocked coordinates are
            last.


        Notes
        -----
        The block averaged `axis` will be moved to the front of the output data.

        See Also
        --------
        reshape
        `moveaxis
        :meth:`reduce`
        """
        self._raise_if_scalar()

        # if block_size is None:
        #     block_size = s
        #     new_shape = self.shape

        #     return (
        #         self.reduce(axis=axis, order=order, parallel=parallel)
        #         # should have single dimension
        #         .reshape()

        axis = self._wrap_axis(axis)
        n = self.shape[axis]

        if block_size is None:
            block_size = n

        nblock = n // block_size

        by = np.arange(nblock).repeat(block_size)
        if len(by) != n:
            by = np.pad(by, (0, n - len(by)), mode="constant", constant_values=-1)

        return self.reduce(axis=axis, by=by, order=order, parallel=parallel)

    # ** Manipulation -------------------------------------------------------------
    @docfiller.decorate
    def reshape(
        self: CentralMoments[T_Float2],
        shape: tuple[int, ...],
        *,
        order: ArrayOrderCFA = None,
    ) -> CentralMoments[T_Float2]:
        """
        Create a new object with reshaped data.

        Parameters
        ----------
        shape : tuple
            shape of values part of data.
        order : {{"C", "F", "A"}}, optional
            Parameter to :func:`numpy.reshape`. Note that this parameter has
            nothing to do with the output data order. Rather, it is how the
            data is read for the reshape.

        Returns
        -------
        output : CentralMoments
            Output object with reshaped data.  This will be a view if possilble;
            otherwise, it will be copy.

        See Also
        --------
        numpy.reshape
        new_like

        Examples
        --------
        >>> from cmomy.random import default_rng
        >>> rng = default_rng(0)
        >>> da = CentralMoments.from_vals(rng.random((10, 2, 3)), mom=2)
        >>> da
        <CentralMoments(val_shape=(10, 2), mom=(2,))>
        array([[[3.    , 0.3159, 0.0603],
                [3.    , 0.5809, 0.1609]],
        <BLANKLINE>
               [[3.    , 0.6266, 0.006 ],
                [3.    , 0.5846, 0.1716]],
        <BLANKLINE>
               [[3.    , 0.5402, 0.1311],
                [3.    , 0.5268, 0.0789]],
        <BLANKLINE>
               [[3.    , 0.2502, 0.0271],
                [3.    , 0.4807, 0.0636]],
        <BLANKLINE>
               [[3.    , 0.6654, 0.064 ],
                [3.    , 0.7723, 0.022 ]],
        <BLANKLINE>
               [[3.    , 0.4042, 0.0511],
                [3.    , 0.519 , 0.0282]],
        <BLANKLINE>
               [[3.    , 0.7698, 0.0406],
                [3.    , 0.4171, 0.0121]],
        <BLANKLINE>
               [[3.    , 0.4413, 0.0122],
                [3.    , 0.5802, 0.0742]],
        <BLANKLINE>
               [[3.    , 0.5679, 0.1174],
                [3.    , 0.3915, 0.1231]],
        <BLANKLINE>
               [[3.    , 0.3122, 0.0153],
                [3.    , 0.3597, 0.1007]]])

               [[10.        ,  0.53720667,  0.05909394],
                [10.        ,  0.42622908,  0.08434857],
                [10.        ,  0.47326641,  0.05907737]]])

        >>> da.reshape(shape=(-1,))
        <CentralMoments(val_shape=(20,), mom=(2,))>
        array([[3.    , 0.3159, 0.0603],
               [3.    , 0.5809, 0.1609],
               [3.    , 0.6266, 0.006 ],
               [3.    , 0.5846, 0.1716],
               [3.    , 0.5402, 0.1311],
               [3.    , 0.5268, 0.0789],
               [3.    , 0.2502, 0.0271],
               [3.    , 0.4807, 0.0636],
               [3.    , 0.6654, 0.064 ],
               [3.    , 0.7723, 0.022 ],
               [3.    , 0.4042, 0.0511],
               [3.    , 0.519 , 0.0282],
               [3.    , 0.7698, 0.0406],
               [3.    , 0.4171, 0.0121],
               [3.    , 0.4413, 0.0122],
               [3.    , 0.5802, 0.0742],
               [3.    , 0.5679, 0.1174],
               [3.    , 0.3915, 0.1231],
               [3.    , 0.3122, 0.0153],
               [3.    , 0.3597, 0.1007]])
        """
        self._raise_if_scalar()
        new_shape = shape + self.mom_shape
        data = self._data.reshape(new_shape, order=order)
        return self.new_like(data=data)

    @docfiller.decorate
    def moveaxis(
        self: CentralMoments[T_Float2],
        source: int | tuple[int, ...],
        destination: int | tuple[int, ...],
        # *,
        # copy: bool = True,
        # order: ArrayOrder | None = None,
    ) -> CentralMoments[T_Float2]:
        """
        Move axis from source to destination.

        Parameters
        ----------
        source : int or sequence of int
            Original positions of the axes to move. These must be unique.
        destination : int or sequence of int
            Destination positions for each of the original axes. These must also be
            unique.
        {copy}

        Returns
        -------
        result : CentralMoments
            CentralMoments object with with moved axes. This array is a view of
            the input array.

        Notes
        -----
        Both ``source`` and ``destination`` are relative to ``self.val_shape``.
        So the moment dimensions will always remain as the last dimensions.


        Examples
        --------
        >>> from cmomy.random import default_rng
        >>> rng = default_rng(0)
        >>> da = CentralMoments.from_vals(rng.random((10, 1, 2, 3)), axis=0, mom=2)
        >>> da.moveaxis((2, 1), (0, 2))
        <CentralMoments(val_shape=(3, 1, 2), mom=(2,))>
        array([[[[10.    ,  0.5205,  0.0452],
                 [10.    ,  0.5238,  0.1272]]],
        <BLANKLINE>
        <BLANKLINE>
               [[[10.    ,  0.4438,  0.0734],
                 [10.    ,  0.628 ,  0.0524]]],
        <BLANKLINE>
        <BLANKLINE>
               [[[10.    ,  0.5038,  0.1153],
                 [10.    ,  0.412 ,  0.0865]]]])

        """
        self._raise_if_scalar()

        def _internal_check_val(v: int | tuple[int, ...]) -> tuple[int, ...]:
            v = (v,) if isinstance(v, int) else tuple(v)
            return tuple(self._wrap_axis(x) for x in v)

        source = _internal_check_val(source)
        destination = _internal_check_val(destination)
        data = np.moveaxis(self.data, source, destination)

        return self.new_like(data=data, verify=False)

    # ** Constructors ----------------------------------------------------------
    @overload  # type: ignore[override]
    @classmethod
    def zeros(  # type: ignore[overload-overlap]
        cls,
        *,
        mom: Moments,
        val_shape: tuple[int, ...] | int | None = ...,
        dtype: None = ...,
        order: ArrayOrderCF | None = ...,
    ) -> CentralMoments[np.float64]: ...
    @overload
    @classmethod
    def zeros(
        cls,
        *,
        mom: Moments,
        val_shape: tuple[int, ...] | int | None = ...,
        dtype: DTypeLikeArg[T_Float2],
        order: ArrayOrderCF | None = ...,
    ) -> CentralMoments[T_Float2]: ...
    @overload
    @classmethod
    def zeros(
        cls,
        *,
        mom: Moments,
        val_shape: tuple[int, ...] | int | None = ...,
        dtype: DTypeLike,
        order: ArrayOrderCF | None = ...,
    ) -> Self: ...

    @classmethod
    @docfiller_abc()
    def zeros(
        cls,
        *,
        mom: Moments,
        val_shape: tuple[int, ...] | int | None = None,
        dtype: DTypeLike = None,
        order: ArrayOrderCF | None = None,
    ) -> CentralMoments[Any] | Self:
        mom_strict, mom_ndim = validate_mom_and_mom_ndim(mom=mom, mom_ndim=None)

        vshape: tuple[int, ...]
        if val_shape is None:
            vshape = ()
        elif isinstance(val_shape, int):
            vshape = (val_shape,)
        else:
            vshape = val_shape

        # add in moments
        mshape: tuple[int, ...] = tuple(m + 1 for m in mom_strict)
        shape: tuple[int, ...] = (*vshape, *mshape)

        data = np.zeros(shape, dtype=dtype, order=order)
        return cls(data=data, mom_ndim=mom_ndim)

    @overload
    @classmethod
    def from_vals(
        cls,
        x: ArrayLikeArg[T_Float2],
        *y: ArrayLike,
        mom: Moments,
        weight: ArrayLike | None = ...,
        axis: int | None = ...,
        order: ArrayOrder = ...,
        parallel: bool | None = ...,
        dtype: None = ...,
    ) -> CentralMoments[T_Float2]: ...
    # dtype
    @overload
    @classmethod
    def from_vals(
        cls,
        x: Any,
        *y: ArrayLike,
        mom: Moments,
        weight: ArrayLike | None = ...,
        axis: int | None = ...,
        order: ArrayOrder = ...,
        parallel: bool | None = ...,
        dtype: DTypeLikeArg[T_Float2],
    ) -> CentralMoments[T_Float2]: ...
    # fallback
    @overload
    @classmethod
    def from_vals(
        cls,
        x: Any,
        *y: ArrayLike,
        mom: Moments,
        weight: ArrayLike | None = ...,
        axis: int | None = ...,
        order: ArrayOrder = ...,
        parallel: bool | None = ...,
        dtype: DTypeLike = ...,
    ) -> Self: ...

    @classmethod
    @docfiller_inherit_abc()
    def from_vals(
        cls,
        x: ArrayLike,
        *y: ArrayLike,
        mom: Moments,
        weight: ArrayLike | None = None,
        axis: int | None = None,
        order: ArrayOrder = None,
        parallel: bool | None = None,
        dtype: DTypeLike = None,
    ) -> CentralMoments[Any] | Self:
        """
        Examples
        --------
        >>> from cmomy.random import default_rng
        >>> rng = default_rng(0)
        >>> x = rng.random((100, 3))
        >>> da = CentralMoments.from_vals(x, axis=0, mom=2)
        >>> da
        <CentralMoments(val_shape=(3,), mom=(2,))>
        array([[1.0000e+02, 5.5313e-01, 8.8593e-02],
               [1.0000e+02, 5.5355e-01, 7.1942e-02],
               [1.0000e+02, 5.1413e-01, 1.0407e-01]])
        """
        axis = -1 if axis is None else axis
        mom_strict, mom_ndim = validate_mom_and_mom_ndim(mom=mom, mom_ndim=None)

        from .reduction import reduce_vals

        data = reduce_vals(
            x,
            *y,
            mom=mom_strict,
            weight=weight,
            axis=axis,
            order=order,
            parallel=parallel,
            dtype=dtype,
        )
        return cls(data=data, mom_ndim=mom_ndim)

    @overload
    @classmethod
    def from_resample_vals(
        cls,
        x: ArrayLikeArg[T_Float2],
        *y: ArrayLike,
        mom: Moments,
        freq: NDArrayInt,
        weight: ArrayLike | None = ...,
        axis: int | None = ...,
        order: ArrayOrder = ...,
        parallel: bool | None = ...,
        dtype: None = ...,
    ) -> CentralMoments[T_Float2]: ...
    @overload
    @classmethod
    def from_resample_vals(
        cls,
        x: Any,
        *y: ArrayLike,
        mom: Moments,
        freq: NDArrayInt,
        weight: ArrayLike | None = ...,
        axis: int | None = ...,
        order: ArrayOrder = ...,
        parallel: bool | None = ...,
        dtype: DTypeLikeArg[T_Float2],
    ) -> CentralMoments[T_Float2]: ...
    @overload
    @classmethod
    def from_resample_vals(
        cls,
        x: Any,
        *y: ArrayLike,
        mom: Moments,
        freq: NDArrayInt,
        weight: ArrayLike | None = ...,
        axis: int | None = ...,
        order: ArrayOrder = ...,
        parallel: bool | None = ...,
        dtype: DTypeLike = ...,
    ) -> Self: ...

    @classmethod
    @docfiller_inherit_abc()
    def from_resample_vals(
        cls,
        x: ArrayLike,
        *y: ArrayLike,
        mom: Moments,
        freq: NDArrayInt,
        weight: ArrayLike | None = None,
        axis: int | None = None,
        order: ArrayOrder = None,
        parallel: bool | None = None,
        dtype: DTypeLike = None,
    ) -> CentralMoments[Any]:
        """
        Examples
        --------
        >>> from cmomy.random import default_rng
        >>> from cmomy.resample import random_freq
        >>> rng = default_rng(0)
        >>> ndat, nrep = 10, 3
        >>> x = rng.random(ndat)
        >>> freq = random_freq(nrep=nrep, ndat=ndat)
        >>> da = CentralMoments.from_resample_vals(x, freq=freq, axis=0, mom=2)
        >>> da
        <CentralMoments(val_shape=(3,), mom=(2,))>
        array([[10.    ,  0.5397,  0.0757],
               [10.    ,  0.5848,  0.0618],
               [10.    ,  0.5768,  0.0564]])

        Note that this is equivalent to (though in general faster than)

        >>> from cmomy.resample import freq_to_indices
        >>> indices = freq_to_indices(freq)
        >>> x_resamp = np.take(x, indices, axis=0)
        >>> da = CentralMoments.from_vals(x_resamp, axis=1, mom=2)
        >>> da
        <CentralMoments(val_shape=(3,), mom=(2,))>
        array([[10.    ,  0.5397,  0.0757],
               [10.    ,  0.5848,  0.0618],
               [10.    ,  0.5768,  0.0564]])

        """
        from .resample import resample_vals

        mom_strict, mom_ndim = validate_mom_and_mom_ndim(mom=mom, mom_ndim=None)
        axis = -1 if axis is None else axis
        data = resample_vals(
            x,
            *y,
            freq=freq,
            mom=mom_strict,
            axis=axis,
            weight=weight,
            order=order,
            parallel=parallel,
            dtype=dtype,
        )

        return cls(data=data, mom_ndim=mom_ndim)

    @classmethod
    @docfiller_inherit_abc()
    def from_raw(
        cls,
        raw: NDArray[T_Float],
        *,
        mom_ndim: Mom_NDim,
    ) -> Self:
        """
        Examples
        --------
        >>> from cmomy.random import default_rng
        >>> rng = default_rng(0)
        >>> x = rng.random(10)
        >>> raw_x = (x[:, None] ** np.arange(5)).mean(axis=0)

        >>> dx_raw = CentralMoments.from_raw(raw_x, mom_ndim=1)
        >>> dx_raw.mean()
        0.5505105129032412
        >>> dx_raw.cmom()
        array([ 1.    ,  0.    ,  0.1014, -0.0178,  0.02  ])

        Which is equivalent to creating raw moments from values
        >>> dx_cen = CentralMoments.from_vals(x, axis=0, mom=4)
        >>> dx_cen.mean()
        0.5505105129032413
        >>> dx_cen.cmom()
        array([ 1.    ,  0.    ,  0.1014, -0.0178,  0.02  ])

        But note that calculating using from_raw can lead to
        numerical issues.  For example

        >>> y = x + 10000
        >>> raw_y = (y[:, None] ** np.arange(5)).mean(axis=0)
        >>> dy_raw = CentralMoments.from_raw(raw_y, mom_ndim=1)
        >>> dy_raw.mean() - 10000
        0.5505105129050207

        Note that the central moments don't match!

        >>> np.isclose(dy_raw.cmom(), dx_raw.cmom())
        array([ True,  True,  True, False, False])

        >>> dy_cen = CentralMoments.from_vals(y, axis=0, mom=4)
        >>> dy_cen.mean() - 10000
        0.5505105129032017
        >>> dy_cen.cmom()  # this matches above
        array([ 1.    ,  0.    ,  0.1014, -0.0178,  0.02  ])
        """
        return super().from_raw(raw=raw, mom_ndim=mom_ndim)  # type: ignore[arg-type]
