# -*- coding: utf-8 -*-
import collections
import contextlib
import posixpath
from dataclasses import dataclass
from functools import total_ordering
from math import log

import pkg_resources
from lektor.build_programs import BuildProgram
from lektor.context import get_ctx
from lektor.environment import Expression
from lektor.environment import FormatExpression
from lektor.pluginsystem import Plugin
from lektor.sourceobj import VirtualSourceObject
from lektor.utils import bool_from_string
from lektor.utils import build_url

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


@total_ordering
@dataclass
class TagWeight:

    count: int
    mincount: int
    maxcount: int

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.count < other.count
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.count == other.count
        return NotImplemented

    def linear(self, lower, upper):
        """Map tag with a number between `lower` and `upper`.

        The least used tag is mapped `lower`, the most used tag is mapped `upper`.
        Mapping is done using a linear function.
        """
        if self.mincount == self.maxcount:
            return lower
        return lower + (upper - lower) * (self.count - self.mincount) / (
            self.maxcount - self.mincount
        )

    def lineargroup(self, groups):
        """Map each tag with an item of list `groups`.

        The least used tag is mapped with the first item, the most used tag is mapped with the last item.
        Mapping is done using a linear function.
        """
        return groups[int(round(self.linear(0, len(groups) - 1)))]

    def log(self, lower, upper):
        """Map each tag with a number between `lower` and `upper`.

        The least used tag is mapped `lower`, the most used tag is mapped `upper`.
        Mapping is done using a linear function over the logarithm of tag counts.

        Theorem: The base of the logarithm used in this function is irrelevant.

        Proof (idea of):
            Let t0 and t1 be the tag counts of the least and most used tag,
            a and b the `lower` and `upper` arguments of this function, and l
            the base of the logarithm used in this function. Let t be the tag
            count of an arbitrary tag.
            To what number is t mapped?

            Let f be the linear function such that f(log(t0)/log(l))=a and
            f(log(t1)/log(l))=b.

            The expression of this function is:
            f(x) = ((b-a)×log(l)×x+a×log(t0)-b×log(t1))/(log(t1)-log(t0)).

            Thus, the arbitrary tag t is mapped to f(log(t)/log(l)), and
            the `log(l)` is crossed out and `l` disappears: the number `l`
            is irrelevant.
        """
        if self.mincount == self.maxcount:
            return lower
        return lower + (upper - lower) * log(self.count / self.mincount) / log(
            self.maxcount / self.mincount
        )

    def loggroup(self, groups):
        """Map each tag with an item of list `groups`.

        The least used tag is mapped with the first item, the most used tag is mapped with the last item.
        Mapping is done using a linear function over the logarithm of tag counts.
        """
        return groups[int(round(self.log(0, len(groups) - 1)))]


class TagsPlugin(Plugin):
    name = u"Tags"
    description = u"Lektor plugin to add tags."
    generated = False
    url_map = {}
    reverse_url_map = {}

    def on_setup_env(self, **extra):
        pkg_dir = pkg_resources.resource_filename("lektor_tags", "templates")
        self.env.jinja_env.loader.searchpath.append(pkg_dir)
        self.env.jinja_env.globals["tagweights"] = self.tagweights
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
        return set(tags)

    def ignore_missing(self):
        return bool_from_string(self.get_config().get("ignore_missing"), False)

    def tagcount(self):
        """Map each tag to the number of pages tagged with it."""
        # Count tags, to be aggregated as "tag weights". Note that tags that
        # only appear in non-discoverable pages are ignored.
        tagcount = collections.Counter()
        for page in get_ctx().pad.query(self.get_parent_path()):
            with contextlib.suppress(KeyError, TypeError):
                tagcount.update(page[self.get_tag_field_name()])
        return tagcount

    def tagweights(self):
        """Return the dictionary of tag weights.

        That is:
            - keys are tags (strings);
            - weights are TagWeight objects.

        This function is to be called AFTER the build have started
        (so that ``get_ctx()`` returns something).
        """
        tagcount = self.tagcount()
        if sum(tagcount.values()) == 0:
            return {}

        return {
            tag: TagWeight(count, min(tagcount.values()), max(tagcount.values()))
            for tag, count in tagcount.items()
        }
