import pytest
from _pytest.mark import ParameterSet


def pytest_generate_tests(metafunc):
    # make sure that fixtures made with @parametrize_fixture are always parametrized indirectly
    for marker in metafunc.definition.iter_markers(name="parametrize"):
        argnames, *_ = marker.args
        argnames, _ = ParameterSet._for_parametrize(
            argnames,
            [],
            metafunc.function,
            metafunc.config,
            nodeid=metafunc.definition.nodeid,
        )

        indirect = marker.kwargs.setdefault("indirect", [])

        if indirect is True:
            continue

        fixturemanager = metafunc.definition._request._fixturemanager
        assert isinstance(indirect, list), "indirect must be a list"

        for argname in argnames:
            for fixturedef in fixturemanager._arg2fixturedefs.get(argname, []):
                if getattr(fixturedef.func, "_indirect", False):
                    continue

                if argname not in indirect:
                    indirect.append(argname)
