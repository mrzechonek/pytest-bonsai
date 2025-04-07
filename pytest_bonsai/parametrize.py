import dataclasses
import functools
import inspect
import itertools
import logging
from typing import Any, Callable, Generic, ParamSpec, Protocol, TypeVar, Mapping

import pytest

__all__ = [
    "FixtureRequest",
    "parametrized_fixture",
    "resolve",
    "expand",
]

logger = logging.getLogger("pytest-bonsai")


class expand(list):
    pass


def parametrize_kwargs(fixture_name, **kwargs):
    # convert scalar arguments to one-element lists
    kwargs = {k: v if isinstance(v, expand) else [v] for k, v in kwargs.items()}

    def parametrize():
        for values in itertools.product(*kwargs.values()):
            param_dict = dict(zip(kwargs.keys(), values))
            yield pytest.param(param_dict)

    return pytest.mark.parametrize(fixture_name, list(parametrize()))


def parametrize_arg(fixture_name, arg):
    args = arg if isinstance(arg, expand) else [arg]

    def parametrize():
        for values in args:
            yield pytest.param(values)

    return pytest.mark.parametrize(fixture_name, [pytest.param(arg) for arg in args])


P = ParamSpec("P")
T = TypeVar("T")


class ParametrizedFixture(Protocol[P]):
    @staticmethod
    def parametrize(*args: P.args, **kwargs: P.kwargs) -> Any: ...

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


def resolve(request, func_or_value):
    """
    :param request: The pytest's [FixtureRequest object](https://docs.pytest.org/en/7.1.x/reference/reference.html#request).
    :param func_or_value: The function or value to resolved.
    """
    if not isinstance(func_or_value, Callable):
        return func_or_value

    # parameters might refer to fixtures
    if getattr(func_or_value, "_pytestfixturefunction", None):
        return request.getfixturevalue(func_or_value.__name__)

    # or may be functions taking fixtures
    try:
        parameters = inspect.signature(func_or_value).parameters.values()
    except ValueError:
        # inspect.signature fails in some cases
        kwargs = {}
    else:
        kwargs = {
            parameter.name: request.getfixturevalue(parameter.name)
            for parameter in parameters
            if parameter.default == inspect.Parameter.empty
        }

    return func_or_value(**kwargs)


def parametrized_fixture(model_or_func):
    """
    :param model_or_func: A dataclass, or a function that takes a single parameter called `request`.
    """
    if inspect.isfunction(model_or_func):
        assert inspect.signature(model_or_func).parameters.keys() == {
            "request"
        }, f"{model_or_func.__name__} must take a single parameter called 'request'"

        @functools.wraps(model_or_func)
        def wrapper(*args, request, **kwargs):
            assert hasattr(request, "param"), f"Fixture {request.fixturename} must always be parametrized"
            return resolve(request, request.param)

        fixture = pytest.fixture(wrapper)
        fixture.parametrize = functools.partial(parametrize_arg, wrapper.__name__)
        fixture._indirect = True

        return fixture

    assert dataclasses.is_dataclass(model_or_func), f"{model_or_func.__name__} must be a dataclass"

    def make_param_model(request, **kwargs):
        for name, field in model_or_func.__dataclass_fields__.items():
            value = kwargs.get(name, ...)

            if value is Ellipsis and field.default_factory != dataclasses.MISSING:
                kwargs[name] = resolve(request, field.default_factory)

            if inspect.isfunction(value):
                kwargs[name] = resolve(request, value)

            if isinstance(kwargs.get(name), expand):
                raise NotADirectoryError("Using expand() in default_factory is not supported")

        return model_or_func(**kwargs)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, request, **kwargs):
            try:
                param = getattr(request, "param", {})

                if inspect.isfunction(param):
                    value = resolve(request, param)
                elif isinstance(param, Mapping):
                    # otherwise, make the parameter a dataclass
                    request.param = make_param_model(request, **param)
                    value = func(*args, request=request, **kwargs)
                else:
                    raise TypeError(
                        f"Invalid parameter type {type(param)} for fixture "
                        f"{func.__module__}.{func.__name__}, expected function or a mapping"
                    )

                logger.debug(
                    "%s.%s(request.param=%r) -> %r",
                    func.__module__,
                    func.__name__,
                    request.param,
                    value,
                )

                return value

            except TypeError as ex:
                raise TypeError(f"Cannot parametrize fixture {func.__name__}") from ex

        fixture = pytest.fixture(wrapper)
        fixture.parametrize = functools.partial(parametrize_kwargs, wrapper.__name__)
        fixture._indirect = True

        return fixture

    return decorator


class FixtureRequest(pytest.FixtureRequest, Generic[T]):
    param: T
