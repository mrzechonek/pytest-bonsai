import pytest
from pytest_bonsai import resolve

from .fixtures import forty_two, twenty_four, not_a_fixture


class TestResolve:
    def test_value(self, request):
        assert resolve(request, 24) == 24

    def test_fixture(self, request):
        assert resolve(request, forty_two) == 42

    def test_lambda(self, request):
        assert resolve(request, lambda forty_two, twenty_four: forty_two + twenty_four) == 66

    def test_lambda_noarg(self, request):
        assert resolve(request, lambda: 42) == 42

    def test_lambda_defaults(self, request):
        assert resolve(request, lambda x=42: x) == 42

    def test_function(self, request):
        assert resolve(request, not_a_fixture) == 66

    def test_builtin(self, request):
        assert resolve(request, list) == []

    def test_invalid(self, request):
        with pytest.raises(pytest.FixtureLookupError, match="not_a_fixture"):
            assert resolve(request, lambda not_a_fixture: not_a_fixture)
