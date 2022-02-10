# Lektor Tags Plugin

[![PyPI version](https://badge.fury.io/py/lektor-tags.svg)](https://pypi.org/project/lektor-tags/)
<a href="https://github.com/ambv/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

## Introduction

This plugin implements tagging for your site. For each of your tags, it builds a page displaying a list of items that have that tag. This can be used for standard tag-based blog navigation. With this plugin you can give any number of tags to any blog posts, and a page will be created for each tag.

For example, if your site has blog posts in your `content/blog` directory tagged with `coffee` and `tea`:

```
name: First Post
---
tags:

coffee
tea
```

The `lektor-tags` plugin builds pages at these URLs:

* `/blog/tag/coffee/`
* `/blog/tag/tea/`

Each page can list all the posts with that tag.

## Installation

Add lektor-tags to your project from command line:

```shell
lektor plugins add lektor-tags
```

See [the Lektor documentation for more instructions on installing plugins](https://www.getlektor.com/docs/plugins/).

## Overview

Say you have a "blog-post" model like this:

```ini
[model]
name = Blog Post

[fields.tags]
type = strings
```

Make a `blog-post.html` template that includes:

```html
{% if this.tags %}
  <ul>
    {% for t in this.tags -%}
      <li>
        <a href="{{ ('/blog@tag/' ~ t)|url }}">
          All posts tagged {{ t }}
        </a>
      </li>
    {% endfor %}
  </ul>
{% endif %}
```

This expression in the template generates a *source path* for each of the blog post's tags:

```jinja
'/blog@tag/' ~ t
```

Then if the tag is "my-tag", the expression renders a source path like:

```
/blog/tag/my-tag
```

A Lektor source path becomes an actual URL using the `url` filter. So the template generates URLs to tag pages like:

```
<a href="{{ ('/blog@tag/' ~ t)|url }}"></a>
```

This uses the source path expression from before, but pipes it through `url` to generate an actual link from the blog post to a tag page.

## Configuration

Set these options in `configs/tags.ini`:

### `parent`

Required. The source path of the tag pages' parent page. For example:

```ini
parent = /blog
```

Then tag pages' source paths are like:

```
/blog/tag/my-tag
```

You can specify the root as the parent:

```ini
parent = /
```

### `items`

A query for all items on the page for one tag. You can use the variables `site` and `tag`. The template's `this` variable has a `parent` attribute. The default query is:

```ini
items = this.parent.children.filter(F.tags.contains(tag))
```

You can sort and filter with any expression:

```ini
items = this.parent.children.filter(F.tags.contains(tag) and F.status == 'published').order_by('-pub_date')
```

If the parent page has [a pagination query](https://www.getlektor.com/docs/guides/pagination/) you may want to use it for tagged pages:

```ini
items = this.parent.pagination.items.filter(F.tags.contains(tag))
```

See [the Lektor documentation for queries](https://www.getlektor.com/docs/api/db/query/).

### `tags_field`

The name of the field in your model that contains tags. Defaults to `tags`. The field should be of type `strings`. See [the Lektor documentation for the `strings` type](https://www.getlektor.com/docs/api/db/types/strings/).

For example, if your model is like:

```ini
[fields.labels]
type = strings
```

Then add this to `tags.ini`:

```ini
tags_field = labels
```

### `template`

The template for the page that lists all posts with a certain tag. The template's `this` variable has attributes `tag` and `items`. An example template:

```html
<h1>Tag: {{ this.tag }}</h1>
<h1>Items:</h1>
<ul>
  {% for i in this.items %}
    <li><a href="{{ i|url }}">{{ i._id }}</a></li>
  {% else %}
    <li><em>No items.</em></li>
  {% endfor %}
</ul>
```

Save a file like this to your project's `templates/tags.html`. If you name the file something different, like `label.html`, add this line to `tags.ini`:

```ini
template = label.html
```

The plugin provides a default template if you don't specify one.

### `url_path`

An expression for the location of each tag page. You can use the variables `site` and `tag`. The `this` variable is a page with attributes `parent` and `items`. The default expression is:

```ini
url_path = {{ this.parent.url_path }}tag/{{ tag }}
```

This expression generates URLs like `/blog/tag/coffee`.

### `ignore_missing`

Default false. To set true, add this line to `tags.ini`:

```ini
ignore_missing = true
```

This allows URLs to missing tag pages to be silently replaced with "". The example use case is if your `blog-post.html` template includes a statement like:

```html
{% for t in this.tags -%}
  <a href="{{ ('/blog@tag/' ~ t)|url }}">{{ t }}</a>
{% endfor %}
```

If a blog post *draft* is not discoverable, and it has any new tags used by no published blog posts, then those tag pages do not yet exist. Turn on `ignore_missing` to allow such drafts to be built. The tag-page URL path will be the empty string "", until the draft is published and the tag page is created.

### `tags`

Advanced configuration. An expression for the set of tags. Note that this expression is also useful in a template to get a list of all tags. The default expression is:

```ini
tags = parent.children.distinct("tags")
```

If you set `tags_field` to a different field name than "tags", the default expression uses your custom field name. For example if you have this line in `tags.ini`:

```ini
tags_field = labels
```

Then the default value of `tags` is:

```ini
tags = parent.children.distinct("labels")
```

You can use any template expression. For example, if your items have a "published" boolean field, you can select tags of published items:

```ini
tags = parent.children.filter(F.published).distinct("tags")
```

Or even list your tags manually:

```ini
tags = ["tag1", "tag2"]
```

See [the Lektor documentation for queries](https://www.getlektor.com/docs/api/db/query/).

Tags are always deduplicated. Tags are sorted in the order listed in the contents.lr / admin, allowing you to control their order manually. Since `{{ tags }}` simply returns a list, you can always apply any Jinja2 filter on that list such as sort, slice, or rejectattr.

## Tag cloud & tag weights

This plugin won't automatically build a tag cloud, but it provides the tools to build it.

The Jinja2 context has a `tagweights()` function, which returns a dictionary that maps tags to their weight using several attributes or functions. Here are those attributes and functions, with examples of how they can be used in a template.

Unused tags are ignored.

### TL;DR Which weight function should I use?

- To get the number of pages tagged by each tag, use `count`.
- To map tags to numbers, use `log(lower, upper)`.
- To map tags to everything else, use `loggroup(list)`.

### `count` — Number of pages tagged with this tag

This is the basic weight, used as a base for the following tags.

#### Example: Tags (with tag count) sorted by tag count (most used first)

```jinja
<ul>
{% for tag, weight in (tagweights() | dictsort(by='value', reverse=true)) %}
    <li>{{ tag }} ({{ weight.count }} articles).</li>
{% endfor %}
</ul>
```

### `linear` — Tags are mapped with a number between `lower` and `upper`.

The less used tag is mapped `lower`, the most used tag is mapped `upper` (`lower` and `upper` can be equal, `upper` can be smaller than `lower`).

Mapping is done using a linear function.

The result is a float: you might want to convert them to integers first (see example for `log`).

Unless you know what you are doing, you should use `log` instead.

### `log` — Logarithm of tag counts are mapped with a number between `lower` and `upper`.

The less used tag is mapped `lower`, the most used tag is mapped `upper` (`lower` and `upper` can be equal, `upper` can be smaller than `lower`).

Mapping is done using a linear function over the logarithm of tag counts.

The result is a float: you might want to convert them to integers first (see example).

#### Example: Most used tag is twice as big as least used tag

```jinja
{% for tag, weight in tagweights()|dictsort %}
<a
    href="{{ ('/blog@tag/' ~ tag)|url }}"
    style="font-size: {{ weight.log(100, 200)|round|int }}%;"
    >
        {{ tag }}
    </a>
{% endfor %}
```

### `lineargroup` — Map each tag with an item of the list given in argument

The less used tag is mapped with the first item, the most used tag is mapped with the last item.

Mapping is done using a linear function.

Unless you know what you are doing, you should use `loggroup` instead.

### `loggroup` — Logarithm of tag counts are mapped with an item of the list given in argument

The less used tag is mapped with the first item, the most used tag is mapped with the last item.

Mapping is done using a linear function over the logarithm of tag counts.

#### Example: Tags are given CSS classes `tagcloud-tiny`, `tagcloud-small`, etc.

```jinja
{% for tag, weight in tagweights()|dictsort %}
<a
    href="{{ ('/blog@tag/' ~ tag)|url }}"
    class="tagcloud-{{ weight.loggroup(["tiny", "small", "normal", "big", "large"]) }}"
    >
        {{ tag }}
    </a>
{% endfor %}
```
