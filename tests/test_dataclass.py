import pytest
from dataclasses import dataclass, field
from pytest_bonsai import parametrized_fixture, expand

from .fixtures import forty_two, twenty_four, not_a_fixture


@dataclass
class School:
    name: str = "Iga"


@parametrized_fixture(School)
def school(request):
    return request.param


@dataclass
class Ninja:
    name: str = "Zuka"
    school: School = field(default_factory=school)


@parametrized_fixture(Ninja)
def ninja(request):
    return request.param


@pytest.fixture
def ninja_name(request):
    return getattr(request, "param", "Kojiro")


class NotADataclass:
    pass


class TestDataclass:
    def test_no_dataclass(self):
        with pytest.raises(AssertionError, match="must be a dataclass"):
            parametrized_fixture(NotADataclass)

    def test_default(self, ninja):
        assert ninja.name == "Zuka"

    @ninja.parametrize(name="Kojiro")
    def test_value(self, ninja):
        assert ninja.name == "Kojiro"

    @ninja.parametrize(name=ninja_name)
    def test_fixture(self, ninja):
        assert ninja.name == "Kojiro"

    @ninja.parametrize(name=lambda: "Kojiro")
    def test_lambda(self, ninja):
        assert ninja.name == "Kojiro"

    @ninja.parametrize(name=expand(["Kojiro", lambda: "Tanaka"]))
    def test_expand(self, ninja):
        assert isinstance(ninja.name, str)

    @ninja.parametrize(name=lambda ninja_name: ninja_name)
    def test_lambda_fixture(self, ninja):
        assert ninja.name == "Kojiro"

    @pytest.mark.parametrize("ninja_name", ["Tanaka"], indirect=True)
    @ninja.parametrize(name=ninja_name)
    def test_inject(self, ninja, ninja_name):
        assert ninja.name == "Tanaka"

    @school.parametrize(name="Toga")
    def test_dependency(self, ninja, school):
        assert ninja.school.name == "Toga"
