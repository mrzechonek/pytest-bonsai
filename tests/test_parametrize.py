import pytest
from pytest_bonsai import parametrized_fixture, expand

from .fixtures import forty_two, twenty_four, not_a_fixture


@parametrized_fixture
def value(request): ...


class TestSimple:
    @pytest.mark.parametrize("value", [24])
    def test_always_indirect(self, value):
        assert value == 24

    @value.parametrize(24)
    def test_scalar(self, value):
        assert value == 24

    @value.parametrize([1, 2, 3])
    def test_list(self, value):
        assert value == [1, 2, 3]

    @value.parametrize(forty_two)
    def test_fixture(self, value):
        assert value == 42

    @value.parametrize(lambda forty_two, twenty_four: forty_two + twenty_four)
    def test_lambda(self, value):
        assert value == 66

    @value.parametrize(lambda: 42)
    def test_lambda_noarg(self, value):
        assert value == 42

    @value.parametrize(not_a_fixture)
    def test_function(self, value):
        assert value == 66

    @value.parametrize(expand([1]))
    def test_expand(self, value):
        assert value == 1

    @value.parametrize(expand([lambda forty_two, twenty_four: forty_two + twenty_four]))
    def test_expand_lambda(self, value):
        assert value == 66
