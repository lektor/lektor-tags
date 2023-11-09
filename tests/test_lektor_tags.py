import os

import flask
import pytest
from lektor.context import Context

app = flask.Flask(__name__)


@pytest.fixture
def build_all(builder):
    failures = builder.build_all()
    assert failures == 0


@pytest.mark.usefixtures("build_all")
def test_builder(pad, builder):
    def get_page(tag):
        path = os.path.join(builder.destination_path, "blog/tag/%s/index.html" % tag)

        return open(path).read().strip()

    assert get_page("tag1") == "tag: tag1, items: post1 post2"
    assert get_page("tag2") == "tag: tag2, items: post1"
    assert get_page("tag3") == "tag: tag3, items: post2"


@pytest.mark.parametrize("tag", ["tag1", "tag3"])
@pytest.mark.usefixtures("build_all")
def test_resolve_url(tag, pad):
    tag_page = pad.resolve_url_path(f"blog/tag/{tag}")
    assert tag_page.tag == tag
    assert tag_page.url_path == f"/blog/tag/{tag}/"


@pytest.mark.usefixtures("build_all")
def test_resolve_url_failure(pad):
    assert pad.resolve_url_path("blog/tag/tag4") is None


def test_virtual_resolver(pad, builder):
    page = pad.get("blog@tag/tag1")
    assert page and page.tag == "tag1"
    url_path = page.url_to(pad.get("blog/post1"))
    assert url_path == "../../post1/"


def test_tags_expression(pad, builder, env):
    with Context(pad=pad):
        plugin = env.plugins["tags"]
        conf = plugin.get_config()
        parent = pad.get("/blog")

        conf["tags"] = 'parent.children.filter(F.published).distinct("tags")'
        assert plugin.get_all_tags(parent) == {"tag1", "tag2"}

        conf["tags"] = '["foo", "bar", "bar"]'
        assert plugin.get_all_tags(parent) == {"bar", "foo"}


def test_default_template(env):
    env.jinja_env.get_template("lektor_tags_default_template.html")
