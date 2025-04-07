# pytest bonsai

<p float="left">
  <a href="https://github.com/mrzechonek/pytest-bonsai/actions/workflows/python-package.yml"><img src="https://github.com/mrzechonek/pytest-bonsai/actions/workflows/python-package.yml/badge.svg"/></a>
  <a href="https://pytest-bonsai.readthedocs.io/"><img src="https://readthedocs.org/projects/pytest-bonsai/badge/?version=latest" alt="Read the Docs"/></a>
  <a href="https://pypi.org/project/pytest-bonsai/"><img src="https://img.shields.io/pypi/v/pytest-bonsai"></a>
</p>

**pytest-bonsai** is a plugin that brings elegant, declarative, and composable
test data to your test suite.

**pytest-bonsai** helps you grow *minimal, yet expressive dependency trees*
using Python dataclasses, fixtures, and dynamic parameter resolution.

## Installation

```
$ pip install pytest-bonsai
```

---

## Showcase

```python
import random
from dataclasses import dataclass, field
from enum import Enum

import pytest

from pytest_bonsai import FixtureRequest, expand, parametrized_fixture


class Rank(Enum):
    GENIN = "Genin"
    CHUNIN = "Chunin"
    JONIN = "Jonin"


class Weapon(Enum):
    KATANA = "Katana"
    KUSARIGAMA = "Kusarigama"
    NUNCHAKU = "Nunchaku"
    SHURIKEN = "Shuriken"
    TANTO = "Tanto"


@dataclass
class Uniform:
    emblem: str
    color: str


@dataclass
class Dojo:
    name: str
    weapons: list[Weapon]
    uniform: Uniform


@dataclass
class Ninja:
    name: str
    rank: Rank
    dojo: Dojo
    weapon: Weapon
    uniform: Uniform

    def __repr__(self):
        return (
            f"{self.name} {self.rank.value}, "
            f"armed with {self.weapon.value}, "
            f"wearing {self.uniform.color} uniform with {self.uniform.emblem}"
        )


# parametrized fixtures act as factories
@dataclass
class DojoParam:
    name: str = field(default_factory=lambda: random.choice(["Konoha", "Kiri", "Kumo"]))
    weapons: list[Weapon] = field(default_factory=lambda: random.sample(list(Weapon), 2))
    uniform_color: str = "black"


@parametrized_fixture(DojoParam)
def dojo(request: FixtureRequest[DojoParam]) -> Dojo:
    return Dojo(
        name=request.param.name,
        weapons=request.param.weapons,
        uniform=Uniform(emblem=f"emblem of {request.param.name}-ryu", color=request.param.uniform_color),
    )


@dataclass
class NinjaParam:
    name: str = field(default_factory=lambda: random.choice(["Hattori", "Goemon", "Kotarou"]))
    rank: Rank = field(default_factory=lambda: random.choice(list(Rank)))
    dojo: Dojo = field(default_factory=dojo)
    weapon: Weapon | None = None
    uniform: Uniform | None = None


@parametrized_fixture(NinjaParam)
def ninja(request: FixtureRequest[NinjaParam]) -> Ninja:
    return Ninja(
        name=request.param.name,
        rank=request.param.rank,
        dojo=request.param.dojo,
        weapon=request.param.weapon or random.choice(request.param.dojo.weapons),
        uniform=request.param.uniform or request.param.dojo.uniform,
    )


# by default, ninjas use dojo's uniform and weapon
def test_ninja_uses_approved_equipment(ninja, dojo):
    assert ninja.weapon in dojo.weapons
    assert ninja.uniform is dojo.uniform


# but can have personal preferences
@ninja.parametrize(weapon=Weapon.KATANA)
def test_sword_ninja(ninja, dojo):
    assert ninja.weapon == Weapon.KATANA


# some are allowed to wear special uniforms
@pytest.fixture
def red_uniform(dojo):
    return Uniform(emblem=dojo.uniform.emblem, color="red")


@ninja.parametrize(uniform=red_uniform)
def test_red_ninja(ninja, dojo):
    assert ninja.uniform.color == "red"


# or choose the color on the fly
@ninja.parametrize(uniform=lambda dojo: Uniform(emblem=dojo.uniform.emblem, color="green"))
def test_green_ninja(ninja, dojo):
    assert ninja.uniform.color == "green"


# some may even choose a diffrent uniform for each assignment
@parametrized_fixture
def color(request): ...


@ninja.parametrize(uniform=lambda dojo, color: Uniform(emblem=dojo.uniform.emblem, color=color))
@color.parametrize(expand(["blue", "pink"]))
def test_rainbow_ninja(ninja, dojo, color):
    assert ninja.uniform.color == color
    assert ninja.uniform.emblem == dojo.uniform.emblem
    assert ninja.weapon in dojo.weapons


# masters have the highest rank, but specialize in weapon of choice
@parametrized_fixture
def master_weapon(request): ...


@ninja.parametrize(rank=Rank.JONIN, weapon=master_weapon)
class TestMasters:
    @master_weapon.parametrize(Weapon.KATANA)
    def test_katana_master(self, ninja, master_weapon):
        assert ninja.rank == Rank.JONIN
        assert ninja.weapon == Weapon.KATANA

    @master_weapon.parametrize(Weapon.TANTO)
    def test_tanto_master(self, ninja, master_weapon):
        assert ninja.rank == Rank.JONIN
        assert ninja.weapon == Weapon.TANTO
```
