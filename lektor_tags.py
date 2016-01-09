# -*- coding: utf-8 -*-
import pkg_resources
import posixpath

from jinja2 import Undefined
from lektor.build_programs import BuildProgram
from lektor.environment import Expression, FormatExpression
from lektor.pluginsystem import Plugin
from lektor.sourceobj import VirtualSourceObject
from lektor.utils import build_url
from werkzeug.utils import cached_property

DEFAULT_ITEMS_QUERY = 'this.parent.children.filter(F.tags.contains(tag))'
DEFAULT_URL_PATH_EXP = '{{ this.parent.url_path }}tag/{{ tag }}'


def _ensure_slash(s):
    return s if s.endswith('/') else s + '/'


class TagPage(VirtualSourceObject):
    def __init__(self, plugin, parent, tag):
        VirtualSourceObject.__init__(self, parent)
        self.plugin = parent.pad.env.plugins['tags']
        self.tag = tag

        # TODO: Must strong-ref the pad?
        self.__pad = parent.pad

    @property
    def items(self):
        items_exp = Expression(self.pad.env, self.plugin.get_items_expression())
        return items_exp.evaluate(self.pad, this=self, values={'tag': self.tag})

    @property
    def path(self):
        return build_url([self.parent.path, '@tag', self.tag])

    @property
    def url_path(self):
        p = TagsPlugin.reverse_url_map[self.path]
        assert p
        return p

    def set_url_path(self, url_path):
        with_slash = _ensure_slash(url_path)
        TagsPlugin.url_map[with_slash] = self
        TagsPlugin.reverse_url_map[self.path] = with_slash

    @property
    def template_name(self):
        return self.plugin.get_template()


class TagPageBuildProgram(BuildProgram):
    def produce_artifacts(self):
        self.declare_artifact(
            posixpath.join(self.source.url_path, 'index.html'),
            sources=list(self.source.iter_source_filenames()))

    def build_artifact(self, artifact):
        artifact.render_template_into(self.source.template_name,
                                      this=self.source)


class TagsPlugin(Plugin):
    name = u'blog-posts'
    description = u'Lektor customization just for emptysqua.re.'
    generated = False
    url_map = {}
    reverse_url_map = {}

    def on_setup_env(self, **extra):
        self.env.add_build_program(TagPage, TagPageBuildProgram)
        parent_path = self.get_parent_path()
        if not parent_path:
            raise RuntimeError('Set the "parent" option in %s'
                               % self.config_filename)

        @self.env.urlresolver
        def tag_resolver(node, url_path):
            u = build_url([node.url_path] + url_path, trailing_slash=True)
            return TagsPlugin.url_map.get(u)

        @self.env.virtualpathresolver('tag')
        def tag_source_path_resolver(node, pieces):
            if node.path == parent_path and len(pieces) == 1:
                return TagPage(self, node, pieces[0])

        @self.env.generator
        def generate_tag_pages(source):
            if source.path != parent_path:
                return

            pad = source.pad
            url_exp = FormatExpression(self.env, self.get_url_path_expression())

            for tag in self.get_all_tags(source):
                page = TagPage(self, source, tag)
                url_path = url_exp.evaluate(pad, this=page, values={'tag': tag})
                page.set_url_path(url_path)
                yield page

    def get_items_expression(self):
        return self.get_config().get('items', DEFAULT_ITEMS_QUERY)

    def get_parent_path(self):
        return self.get_config().get('parent')

    def get_url_path_expression(self):
        return self.get_config().get('url_path', DEFAULT_URL_PATH_EXP)

    def get_template(self):
        filename = self.get_config().get('template')
        if filename:
            return filename

        return self._default_template

    @cached_property
    def _default_template(self):
        stream = pkg_resources.resource_stream('lektor_tags',
                                               'templates/tag.html')
        return self.env.jinja_env.from_string(stream.read())

    def get_tag_field_name(self):
        return self.get_config().get('tags_field', 'tags')

    def get_all_tags(self, parent):
        # TODO: configurable tag filter.
        tag_field = self.get_tag_field_name()
        tags = set()
        for item in parent.children:
            if tag_field not in item:
                # TODO: warn if "verbose" mode.
                continue
            item_tags = item[tag_field]
            if isinstance(item_tags, (list, tuple)):
                tags |= set(item_tags)
            elif not isinstance(item_tags, Undefined):
                tags.add(item_tags)

        return sorted(tags)
