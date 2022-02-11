from collections import Counter

import pytest
from lektor.context import Context

from lektor_tags import TagWeight


@pytest.fixture
def tags_plugin(env):
    return env.plugins["tags"]


@pytest.fixture
def lektor_context(pad):
    with Context(pad=pad) as ctx:
        yield ctx


@pytest.mark.usefixtures("lektor_context")
def test_tagcount(tags_plugin):
    assert tags_plugin.tagcount() == Counter({"tag1": 2, "tag2": 1, "tag3": 1})


@pytest.mark.usefixtures("lektor_context")
def test_tagweights(tags_plugin):
    assert tags_plugin.tagweights() == {
        "tag1": TagWeight(2, 1, 2),
        "tag2": TagWeight(1, 1, 2),
        "tag3": TagWeight(1, 1, 2),
    }


@pytest.mark.usefixtures("lektor_context")
def test_tagweights_no_tags(pad, tags_plugin):
    config = tags_plugin.get_config()
    config["tags_field"] = "test_no_tags"
    assert tags_plugin.tagweights() == {}


@pytest.fixture
def tagweight(count, mincount, maxcount):
    return TagWeight(count, mincount, maxcount)


@pytest.mark.parametrize(
    "count, mincount, maxcount, lower, upper, expected",
    [
        (1, 1, 1, 1, 2, 1),
        (1, 1, 3, 1, 2, 1),
        (2, 1, 3, 1, 2, 1.5),
        (3, 1, 3, 1, 2, 2),
    ],
)
def test_TagWeight_linear(tagweight, lower, upper, expected):
    assert tagweight.linear(lower, upper) == expected


@pytest.mark.parametrize(
    "count, mincount, maxcount, groups, expected",
    [
        (1, 1, 4, ("a", "b"), "a"),
        (2, 1, 4, ("a", "b"), "a"),
        (3, 1, 4, ("a", "b"), "b"),
        (4, 1, 4, ("a", "b"), "b"),
    ],
)
def test_TagWeight_lineargroup(tagweight, groups, expected):
    assert tagweight.lineargroup(groups) == expected


@pytest.mark.parametrize(
    "count, mincount, maxcount, lower, upper, expected",
    [
        (1, 1, 1, 1, 3, 1),
        (1, 1, 4, 1, 3, 1),
        (2, 1, 4, 1, 3, 2),
        (4, 1, 4, 1, 3, 3),
    ],
)
def test_TagWeight_log(tagweight, lower, upper, expected):
    assert tagweight.log(lower, upper) == expected


@pytest.mark.parametrize(
    "count, mincount, maxcount, groups, expected",
    [
        (1, 1, 100, ("a", "b", "c"), "a"),
        (3, 1, 100, ("a", "b", "c"), "a"),
        (12, 1, 100, ("a", "b", "c"), "b"),
        (90, 1, 100, ("a", "b", "c"), "c"),
        (100, 1, 100, ("a", "b", "c"), "c"),
    ],
)
def test_TagWeight_loggroup(tagweight, groups, expected):
    assert tagweight.loggroup(groups) == expected
