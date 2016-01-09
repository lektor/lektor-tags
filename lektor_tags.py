# -*- coding: utf-8 -*-
import pkg_resources
import posixpath

from jinja2 import Undefined
from lektor.build_programs import BuildProgram
from lektor.environment import Expression, FormatExpression
from lektor.pluginsystem import Plugin
from lektor.sourceobj import VirtualSourceObject
from werkzeug.utils import cached_property

DEFAULT_ITEMS_QUERY = 'parent.children.filter(F.tags.contains(tag))'


class TagPage(VirtualSourceObject):
    def __init__(self, parent, tag, items):
        VirtualSourceObject.__init__(self, parent)
        self.plugin = parent.pad.env.plugins['tags']
        self.items = items
        self.tag = tag
        self.__url_path = None

        # TODO: Must strong-ref the pad?
        self.__pad = parent.pad

    @property
    def path(self):
        return posixpath.join(self.parent.path, 'tag', self.tag) + '/'

    @property
    def url_path(self):
        assert self.__url_path
        return self.__url_path

    def set_url_path(self, url_path):
        self.__url_path = url_path

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

    def on_setup_env(self, **extra):
        self.env.add_build_program(TagPage, TagPageBuildProgram)
        parent_path = self.get_parent_path()
        if not parent_path:
            raise RuntimeError('Set the "parent" option in %s'
                               % self.config_filename)

        @self.env.urlresolver
        def tag_resolver(node, url_path):
            # url_path is a list of segments.
            joined_path = posixpath.join(*([node.url_path] + url_path))
            return TagsPlugin.url_map.get(joined_path)

        @self.env.generator
        def generate_tag_pages(source):
            if source.path != parent_path:
                return

            pad = source.pad
            items_exp = Expression(self.env, self.get_items_expression())
            url_exp = FormatExpression(self.env, self.get_url_path_expression())

            for tag in self.get_all_tags(source):
                values = {'parent': source, 'tag': tag}
                values['items'] = items = items_exp.evaluate(pad, values=values)
                page = TagPage(source, tag, items)
                url_path = url_exp.evaluate(pad, this=page, values=values)
                url_path = url_path.rstrip('/')
                page.set_url_path(url_path)
                TagsPlugin.url_map[url_path] = page
                yield page

    def get_items_expression(self):
        return self.get_config().get('items', DEFAULT_ITEMS_QUERY)

    def get_parent_path(self):
        return self.get_config().get('parent')

    def get_url_path_expression(self):
        return self.get_config().get('url_path')

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
