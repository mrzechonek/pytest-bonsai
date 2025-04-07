# pytest bonsai

It's is a plugin that brings elegant, declarative, and composable
test data to your test suite.

It helps you grow *minimal, yet expressive* dependency trees using Python
dataclasses, fixtures, and dynamic parameter resolution.

## Installation

The plugin is available on PyPI and can be installed using pip:

```
$ pip install pytest-bonsai
```

## Usage

Bonsai is built around
[indirect parametrization](https://docs.pytest.org/en/7.1.x/example/parametrize.html#indirect-parametrization),
but instead of using parametrization to multiply the number of test, it uses it
to customize test setup.

Most uses revolve around the `@parametrized_fixture` decorator, which extends
the default `@pytest.fixture` decorator by making sure that

 * fixtures are always parametrized indirectly
 * `request.param` is always available and is an instance of a selected dataclass

Dataclass objects are instantiated by resolving fixtures used in field factories

!!! note "Note"

    This is a slight abuse of the dataclass API, because field factories are not allowed to
    take arguments.

    This means that dataclasses used as parameters cannot (most of the time) be instantiated
    directly.

### A trivial example

At the most basic level, `@parametrized_fixture` is just a wrapper around
`@pytest.fixture` that converts parameter from a dictionary into a dataclass:

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


@pytest.mark.parametrize('user', [dict(name='Bob')])
def test_bob(user: User):
    assert user.name == "Bob"
```

The decorator also adds a `parametrize()` method to the fixture, which is just a
syntactic sugar for `@pytest.mark.parametrize`, so you can also write:

```python
@user.parametrize(name='Bob')
def test_bob(user: User):
    assert user.name == "Bob"
```

### A more interesting case

Things get interesting when `UserParam` dataclass defines field defaults that
depend on other fixtures:

```python
from dataclasses import dataclass, field
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

Field defaults may even be lambdas that take other fixtures as arguments:

```python
from dataclasses import dataclass, field
from pytest_bonsai import parametrized_fixture, FixtureRequest


@dataclass
class User:
    name: str


@pytest.fixture
def username():
    return "Charlie"


@pytest.fixture
def email(username):
    return f"{username.lower}@af.mil"


@dataclass
class UserParam:
    name: str = field(default_factory=lambda username, email: f'{username} <{email}>')


@pytest.mark.parametrize("username", ["Derek"], indirect=True)
def test_derek(username, user):
    assert user.name == "Derek <derek@af.mil>"
```

### Always-indirect fixtures

Calling `@parametrized_fixture` without any arguments makes the fixture always
indirect, and return the parameter:

```python
from pytest_bonsai import parametrized_fixture


@parametrized_fixture
def username(request): ...


@username.parametrize('Edward')
def test_edward(username):
    assert username == 'Edward'
```

While by itself it's not very useful, it makes it easier to define extension
points like `username` from the previous example:

```python
from dataclasses import dataclass, field
from pytest_bonsai import parametrized_fixture, FixtureRequest


@dataclass
class User:
    name: str


@parametrized_fixture
def username(request): ...


@pytest.fixture
def email(username):
    return f"{username.lower}@af.mil"


@dataclass
class UserParam:
    name: str = field(default_factory=lambda username, email: f'{username} <{email}>')


@username.parametrize("Derek")
def test_derek(username, user):
    assert user.name == "Derek <derek@af.mil>"
```

### Extension points

An extension point may also be injected into a parameter that is not explicitly
prepared for it, so don't need to plan the whole dependency tree in advance:

```python
from dataclasses import dataclass
from pytest_bonsai import parametrized_fixture, FixtureRequest


@dataclass
class User:
    name: str


@parametrized_fixture
def username(request): ...


@dataclass
class UserParam:
    name: str = "Alice"


@parametrized_fixture(User)
def user(request: FixtureRequest[UserParam]) -> User:
    return User(name=request.param.name)


@user.parametrize(name=username)
@username.parametrize("Derek")
def test_derek(username, user):
    assert user.name == "Derek"
```
