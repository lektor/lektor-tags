# Lektor Tags Plugin

This plugin implements tagging for your site. For each of your tags, it builds a page with a list of pages that have that tag. This can be used for standard tag-based blog navigation.

For example, if your site has blog posts like this in your `contents/blog` directory:

```
name: First Post
---
tags:

coffee
tea
```

Create a `configs/tags.ini`, like:

```
parent = /blog
template = tags.html
```

The `lektor-tags` plugin will render pages at these URLs:

* `blog/tag/coffee/`
* `blog/tag/tea/`

Each page lists all the posts with that tag.

## Installation

Add lektor-tags to your project from command line:

```
lektor plugins add lektor-tags
```

See [the Lektor documentation for more instructions on installing plugins](https://www.getlektor.com/docs/plugins/).

## Configuration

Set these options in `configs/tags.ini`:

### `parent`

Required. The source path of the tag pages' parent page.

### `items`

A query for all items on the page for one tag. You can use the variables `site` and `tag`. The template's `this` variable has a `parent` attribute. The default query is:

```
items = this.parent.children.filter(F.tags.contains(tag))
```

You can sort and filter with any expression:

```
items = this.parent.children.filter(F.tags.contains(tag) and F.status == 'published').order_by('-pub_date')
```

See [the Lektor documentation for queries](https://www.getlektor.com/docs/api/db/query/).

### `tags_field`

The name of the field in your model that contains tags. Defaults to `tags`. The field should be of type `strings`. See [the Lektor documentation for the `strings` type](https://www.getlektor.com/docs/api/db/types/strings/).

For example, if your model is like:

```
[fields.labels]
type = strings
```

Then add this to `tags.ini`:

```
tags_field = labels
```

### `template`

The template for the page that lists all posts with a certain tag. The template's `this` variable has attributes `tag` and `items`. An example template:

```
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

```
template = label.html
```

The plugin provides a default template if you don't specify one.

### `url_path`

An expression for the location of each tag page. You can use the variables `site` and `tag`. The `this` variable is a page with attributes `parent` and `items`. The default expression is:

```
url_path = {{ this.parent.url_path }}tag/{{ tag }}
```

This expression generates URLs like `/blog/tag/coffee`.

### `tags`

Advanced configuration. An expression for the set of tags. The default expression is:

```
tags = parent.children.distinct("tags")
```

If you set `tags_field` to a different field name than "tags", the default expression uses your custom field name. For example if you have this line in `tags.ini`:

```
tags_field = labels
```

Then the default value of `tags` is:

```
tags = parent.children.distinct("labels")
```

You can use any template expression. For example, if your items have a "published" boolean field, you can select tags of published items:

```
tags = parent.children.filter(F.published).distinct("tags")
```

Or even list your tags manually:

```
tags = ["tag1", "tag2"]
```

See [the Lektor documentation for queries](https://www.getlektor.com/docs/api/db/query/).

Tags are always deduplicated, and alphabetically ordered.
