# pytest bonsai

**pytest-bonsai** is a plugin that brings elegant, declarative, and composable
test data to your test suite.

**pytest-bonsai** helps you grow *minimal, yet expressive dependency trees*
using Python dataclasses, fixtures, and dynamic parameter resolution.

## Installation

```
$ pip install pytest-bonsai
```

---

## Basics: Dataclass Fixtures

Bonsai is built around [indirect
parametrization](https://docs.pytest.org/en/7.1.x/example/parametrize.html#indirect-parametrization),
but instead of using parametrization to multiply the number of test, it uses it to customize test setup.

### A trivial example

```python
from dataclasses import dataclass

from pytest_bonsai import parametrized_fixture, FixtureRequest


@dataclass
class User:
    name: str


@dataclass
class UserParam:
    name: str = "Alice"


@parametrized_fixture(User)
def user(request: FixtureRequest[UserParam]) -> User:
    return User(
        name=request.param.name,
    )


def test_alice(user: User):
    assert user.name == "Alice"


@user.parametrize(name="Bob")
def test_bob(user: User):
    assert user.name == "Bob"
```


### A more interesting case

The `UserParam` dataclass can use other fixtures to set its default values:

```python
from dataclasses import dataclass
import pytest

from pytest_bonsai import parametrized_fixture, FixtureRequest


@dataclass
class User:
    name: str


@pytest.fixture
def username():
    return "Charlie"


@dataclass
class UserParam:
    name: str = field(default_factory=username)


@parametrized_fixture(User)
def user(request: FixtureRequest[UserParam]) -> User:
    return User(
        name=request.param.name,
    )


def test_charlie(user):
    assert user.name == "Charlie"


@pytest.mark.parametrize("username", ["Derek"], indirect=True)
def test_derek(user):
    assert user.name == "Derek"
```

### Always-indirect fixtures

Calling `@parametrized_fixture` without any arguments makes the fixture always
indirect, and return the parameter:

```python
from pytest_bonsai import parametrized_fixture


@parametrized_fixture
def email(request): ...


@email.parametrize('edward@af.mil')
def test_edward(email):
    assert email == 'edward@af.mi')
```

While by itself it's not very useful, it makes it easier to define extension
points like `username` from the previous example and `email` in the next one.

### Even more interesting: lambdas that take fixtures

```python
from dataclasses import dataclass, field
import pytest

from pytest_bonsai import parametrized_fixture, FixtureRequest


@dataclass
class User:
    name: str


@parametrized_fixture
def email(request): ...


@dataclass
class UserParam:
    name: str = field(default_factory=username)


@parametrized_fixture(User)
def user(request: FixtureRequest[UserParam]) -> User:
    return User(
        name=request.param.name,
    )


def test_charlie(user):
    assert user.name == "Charlie"


@user.parametrize(name=lambda email: email.split('@')[0].title())
@email.parametrize('edward@af.mil')
def test_edward(user):
    assert user.name == "Edward"
```
