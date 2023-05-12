<!-- markdownlint-disable MD041 -->

[![Repo][repo-badge]][repo-link] [![Docs][docs-badge]][docs-link]
[![PyPI license][license-badge]][license-link]
[![PyPI version][pypi-badge]][pypi-link]
[![Conda (channel only)][conda-badge]][conda-link]
[![Code style: black][black-badge]][black-link]

<!--
  For more badges, see
  https://shields.io/category/other
  https://naereen.github.io/badges/
  [pypi-badge]: https://badge.fury.io/py/cmomy
-->

[black-badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-link]: https://github.com/psf/black
[pypi-badge]: https://img.shields.io/pypi/v/cmomy
[pypi-link]: https://pypi.org/project/cmomy
[docs-badge]: https://img.shields.io/badge/docs-sphinx-informational
[docs-link]: https://pages.nist.gov/cmomy/
[repo-badge]: https://img.shields.io/badge/--181717?logo=github&logoColor=ffffff
[repo-link]: https://github.com/usnistgov/cmomy
[conda-badge]: https://img.shields.io/conda/vn/conda-forge/cmomy.svg
[conda-link]: https://anaconda.org/conda-forge/cmomy
[license-badge]: https://img.shields.io/pypi/l/cmomy?color=informational
[license-link]: https://github.com/usnistgov/cmomy/blob/main/LICENSE

<!-- [conda-badge]: https://img.shields.io/conda/v/wpk-nist/cmomy -->
<!-- [conda-link]: https://anaconda.org/wpk-nist/cmomy -->
<!-- other links -->

[numpy]: https://numpy.org
[Numba]: https://numba.pydata.org/
[xarray]: https://docs.xarray.dev/en/stable/

# cmomy

A Python package to calculate and manipulate Central (co)moments. The main
features of `cmomy` are as follows:

- [Numba][Numba] accelerated computation of central moments and co-moments
- Routines to combine, and resample central moments.
- Both [numpy][numpy] array-like and [xarray][xarray] DataArray interfaces to
  Data.
- Routines to convert between central and raw moments.

## Overview

`cmomy` is an open source package to calculate central moments and co-moments in
a numerical stable and direct way. Behind the scenes, `cmomy` makes use of
[Numba][Numba] to rapidly calculate moments. A good introduction to the type of
formulas used can be found
[here](https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance).

## Features

- Fast calculation of central moments and central co-moments with weights
- Support for scalar or vector inputs
- numpy and xarray api's
- bootstrap resampling

## Status

This package is actively used by the author. Please feel free to create a pull
request for wanted features and suggestions!

## Quick start

Use one of the following

```bash
pip install cmomy
```

or

```bash
conda install -c conda-forge cmomy
```

## Example usage

```pycon
>>> import numpy as np
>>> import cmomy

>>> np.random.seed(0)
>>> x = np.random.rand(100)
>>> m = x.mean()
>>> mom = np.array([((x - m) ** i).mean() for i in range(4)])
>>> c = cmomy.CentralMoments.from_vals(x, mom=3)

>>> np.testing.assert_allclose(c.cmom(), mom, atol=1e-8)
>>> c.cmom()
array([1.    , 0.    , 0.0831, 0.0016])

# break up into chunks
>>> c = cmomy.CentralMoments.from_vals(x.reshape(-1, 2), mom=3)

>>> c
<CentralMoments(val_shape=(2,), mom=(3,))>
array([[5.0000e+01, 5.0013e-01, 7.9827e-02, 2.1156e-03],
       [5.0000e+01, 4.4546e-01, 8.4914e-02, 1.5954e-03]])

# Reduce along an axis
>>> c.reduce(axis=0).cmom()
array([1.    , 0.    , 0.0831, 0.0016])

# unequal chunks
>>> x0, x1, x2 = x[:20], x[20:60], x[60:]

>>> cs = [cmomy.CentralMoments.from_vals(_, mom=3) for _ in (x0, x1, x2)]

>>> c = cs[0] + cs[1] + cs[2]

>>> np.testing.assert_allclose(c.cmom(), mom, atol=1e-8)
>>> c.cmom()
array([1.    , 0.    , 0.0831, 0.0016])

```

## Note on caching

This code makes extensive use of the numba python package. This uses a jit
compiler to speed up vital code sections. This means that the first time a
function called, it has to compile the underlying code. However, caching has
been implemented. Therefore, the very first time you run a function, it may be
slow. But all subsequent uses (including other sessions) will be already
compiled.

A quick way to cache (most all) the [Numba][Numba] functions is to run the
tests. This can be done with

```bash
conda/mamba/pip install pytest

pytest --pyargs cmomy
```

<!-- end-docs -->

## Documentation

See the [documentation][docs-link] for a look at `cmomy` in action.

## License

This is free software. See [LICENSE][license-link].

## Related work

This package is used extensively in the newest version of `thermoextrap`. See
[here](https://github.com/usnistgov/thermo-extrap).

## Contact

The author can be reached at wpk@nist.gov.

## Credits

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[wpk-nist-gov/cookiecutter-pypackage](https://github.com/wpk-nist-gov/cookiecutter-pypackage)
Project template forked from
[audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage).
