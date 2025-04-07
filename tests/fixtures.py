import pytest


@pytest.fixture
def forty_two():
    return 42


@pytest.fixture
def twenty_four():
    return 24


def not_a_fixture():
    return 66
