# -*- coding: utf-8 -*-
import pkg_resources
import posixpath

from lektor.build_programs import BuildProgram
from lektor.environment import Expression, FormatExpression
from lektor.pluginsystem import Plugin
from lektor.sourceobj import VirtualSourceObject
from lektor.utils import build_url, bool_from_string

DEFAULT_ITEMS_QUERY = "this.parent.children.filter(F.tags.contains(tag))"
DEFAULT_URL_PATH_EXP = "{{ this.parent.url_path }}tag/{{ tag }}"


def _ensure_slash(s):
    return s if s.endswith("/") else s + "/"


class TagPage(VirtualSourceObject):
    def __init__(self, parent, tag):
        VirtualSourceObject.__init__(self, parent)
        self.plugin = parent.pad.env.plugins["tags"]
        self.tag = tag
        self.i_want_to_live = self.pad  # See lektor-tags/issues/2

    @property
    def items(self):
        items_exp = Expression(self.pad.env, self.plugin.get_items_expression())
        return items_exp.evaluate(self.pad, this=self, values={"tag": self.tag})

    @property
    def path(self):
        return build_url([self.parent.path, "@tag", self.tag])

    @property
    def url_path(self):
        try:
            return TagsPlugin.reverse_url_map[self.path]
        except KeyError:
            if self.plugin.ignore_missing():
                return ""
            raise

    def set_url_path(self, url_path):
        with_slash = _ensure_slash(url_path)
        TagsPlugin.url_map[with_slash] = self
        TagsPlugin.reverse_url_map[self.path] = with_slash

    @property
    def template_name(self):
        return self.plugin.get_template_filename()


class TagPageBuildProgram(BuildProgram):
    def produce_artifacts(self):
        self.declare_artifact(
            posixpath.join(self.source.url_path, "index.html"),
            sources=list(self.source.iter_source_filenames()),
        )

    def build_artifact(self, artifact):
        artifact.render_template_into(self.source.template_name, this=self.source)


class TagsPlugin(Plugin):
    name = u"Tags"
    description = u"Lektor plugin to add tags."
    generated = False
    url_map = {}
    reverse_url_map = {}

    def on_setup_env(self, **extra):
        pkg_dir = pkg_resources.resource_filename("lektor_tags", "templates")
        self.env.jinja_env.loader.searchpath.append(pkg_dir)
        self.env.add_build_program(TagPage, TagPageBuildProgram)

        @self.env.urlresolver
        def tag_resolver(node, url_path):
            if not self.has_config():
                return

            u = build_url([node.url_path] + url_path, trailing_slash=True)
            return TagsPlugin.url_map.get(u)

        @self.env.virtualpathresolver("tag")
        def tag_source_path_resolver(node, pieces):
            if not self.has_config():
                return

            if node.path == self.get_parent_path() and len(pieces) == 1:
                return TagPage(node, pieces[0])

        @self.env.generator
        def generate_tag_pages(source):
            if not self.has_config():
                return

            parent_path = self.get_parent_path()
            if source.path != parent_path:
                return

            pad = source.pad
            url_exp = FormatExpression(self.env, self.get_url_path_expression())

            for tag in self.get_all_tags(source):
                page = TagPage(source, tag)
                url_path = url_exp.evaluate(pad, this=page, values={"tag": tag})
                page.set_url_path(url_path)
                yield page

    def has_config(self):
        return not self.get_config().is_new

    def get_items_expression(self):
        return self.get_config().get("items", DEFAULT_ITEMS_QUERY)

    def get_tags_expression(self):
        tags_exp = self.get_config().get("tags")
        if tags_exp:
            return tags_exp

        return 'parent.children.distinct("%s")' % self.get_tag_field_name()

    def get_parent_path(self):
        p = self.get_config().get("parent")
        if not p:
            raise RuntimeError('Set the "parent" option in %s' % self.config_filename)

        return p

    def get_url_path_expression(self):
        return self.get_config().get("url_path", DEFAULT_URL_PATH_EXP)

    def get_template_filename(self):
        filename = self.get_config().get("template")
        if filename:
            return filename

        return "lektor_tags_default_template.html"

    def get_tag_field_name(self):
        return self.get_config().get("tags_field", "tags")

    def get_all_tags(self, parent):
        exp = Expression(self.env, self.get_tags_expression())
        tags = exp.evaluate(parent.pad, values={"parent": parent})
        return sorted(set(tags))

    def ignore_missing(self):
        return bool_from_string(self.get_config().get("ignore_missing"), False)
