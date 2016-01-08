# -*- coding: utf-8 -*-
import posixpath

from lektor.build_programs import BuildProgram
from lektor.environment import Expression, FormatExpression
from lektor.pluginsystem import Plugin
from lektor.sourceobj import VirtualSourceObject


DEFAULT_ITEMS_QUERY = 'parent.children.filter(F.tags.contains(tag))'


class TagPage(VirtualSourceObject):
    # TODO: shouldn't need parent passed in?
    # TODO: track dependencies
    def __init__(self, parent, tag, items):
        VirtualSourceObject.__init__(self, parent)
        self.plugin = parent.pad.env.plugins['tags']
        self.items = list(items)
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
        return self.plugin.get_template_name()


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

        @self.env.urlresolver
        def tag_resolver(node, url_path):
            # url_path is a list of segments.
            joined_path = posixpath.join(*([node.url_path] + url_path))
            return TagsPlugin.url_map.get(joined_path)

        @self.env.generator
        def generate_tag_pages(source):
            if TagsPlugin.generated:
                return

            TagsPlugin.generated = True
            pad = source.pad
            env = pad.env
            parent_exp = Expression(env, self.get_parent_expression())
            if not parent_exp:
                raise RuntimeError('Set the "parent" option in %s'
                                   % self.config_filename)

            parent = parent_exp.evaluate(pad)

            items_exp = Expression(env, self.get_items_expression())
            url_exp = FormatExpression(env, self.get_url_path_expression())

            for tag in ['tag1', 'tag2', 'tag3']: # todo:
                values = {'parent': parent, 'tag': tag}

                # TODO: "this"?
                values['items'] = items = items_exp.evaluate(pad, values=values)
                page = TagPage(parent, tag, items)
                url_path = url_exp.evaluate(pad, this=page, values=values)
                url_path = url_path.rstrip('/')
                page.set_url_path(url_path)
                TagsPlugin.url_map[url_path] = page
                yield page

    def get_items_expression(self):
        return self.get_config().get('items', DEFAULT_ITEMS_QUERY)

    def get_parent_expression(self):
        return self.get_config().get('parent')

    def get_url_path_expression(self):
        return self.get_config().get('url_path')

    def get_template_name(self):
        # TODO: test
        return self.get_config().get('template', 'tag.html')

    # def get_all_tags(self, blog):
    #     tag_field = self.get_tag_field_name()
    #     model_id = self.get_tag_model()
    #     tags = set()
    #     for item in blog.children:
    #         if item.datamodel.id != model_id:
    #             continue
    #         if tag_field not in item:
    #             continue
    #         item_tags = item[tag_field]
    #         if isinstance(item_tags, (list, tuple)):
    #             tags |= set(item_tags)
    #         elif not isinstance(item_tags, Undefined):
    #             tags.add(item_tags)
    #
    #     return sorted(tags)
