import os

import flask
from lektor.context import Context

app = flask.Flask(__name__)


def test_builder(pad, builder):
    failures = builder.build_all()
    assert not failures

    def get_page(tag):
        path = os.path.join(builder.destination_path,
                            'blog/tag/%s/index.html' % tag)

        return open(path).read().strip()

    assert get_page('tag1') == 'tag: tag1, items: post1 post2'
    assert get_page('tag2') == 'tag: tag2, items: post1'
    assert get_page('tag3') == 'tag: tag3, items: post2'


def test_resolver(pad, builder, webui):
    failures = builder.build_all()
    assert not failures

    info = webui.lektor_info

    def resolve(to_resolve):
        with app.test_request_context(to_resolve):
            return info.resolve_artifact(to_resolve, pad=pad)

    def check_tag(tag):
        artifact = 'blog/tag/%s/index.html' % tag
        artifact_path = os.path.join(info.output_path, artifact)
        url_path = 'blog/tag/%s/' % tag
        assert resolve(url_path) == (artifact, artifact_path)

    check_tag('tag1')
    check_tag('tag2')
    check_tag('tag3')
    assert resolve('blog/tag/tag4/')[0] is None


def test_virtual_resolver(pad, builder):
    page = pad.get('blog@tag/tag1')
    assert page and page.tag == 'tag1'
    url_path = page.url_to(pad.get('blog/post1'))
    assert url_path == '../../../blog/post1/'


def test_tags_expression(pad, builder, env):
    with Context(pad=pad):
        plugin = env.plugins['tags']
        conf = plugin.get_config()
        parent = pad.get('/blog')

        conf['tags'] = 'parent.children.filter(F.published).distinct("tags")'
        assert plugin.get_all_tags(parent) == ['tag1', 'tag2']

        conf['tags'] = '["foo", "bar", "bar"]'
        assert plugin.get_all_tags(parent) == ['bar', 'foo']
