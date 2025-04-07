
# Bonsai API

## pytest_bonsai.resolve

Resolve the passed argument in the context of the current `FixtureRequest`.

 * When passed a **value**, it will be returned as is.
 * When passed a **fixture**, will evaulate the fixture for the current request.
 * When passed a **function taking (non-default) arguments**, will inspect
   the argument names, then (recursively) resolve fixtures witch matching names,
   and finally call the function with resolved arguments.

!!! note "Note"
    This is the low level interface to the whole machinery.

::: pytest_bonsai.resolve


## pytest_bonsai.parametrized_fixture

The argument-less variant: when applied to a function, creates a fixture which
resolves its parameter via `pytest_bonsai.resolve`.

!!! note "Note"
    All tests using such a fixture must be parametrized.

!!! warning "Warning"
    The decorated function will not be called, because the value
    always comes from the parameter.


## pytest_bonsai.parametrized_fixture(_dataclass_)

Variant with an argument: when applied to a function, creates a fixture which
expects the parameter to be a dictionary and wraps it in a specified dataclass,
resolving all intermediate values via `pytest_bonsai.resolve`.

::: pytest_bonsai.parametrized_fixture
