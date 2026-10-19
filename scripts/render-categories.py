"""Render homepage categories from all published posts, including later pages."""

import json
import sys
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup


CATEGORY_STYLE = """
.homeCategories{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}
.homeCategory{display:inline-flex;align-items:center;justify-content:center;
min-height:32px;box-sizing:border-box;padding:4px 12px;border:1px solid #3f5668;
border-radius:999px;background:transparent;color:#3f5668;text-decoration:none;
font-size:14px;font-weight:600;line-height:1.4;overflow-wrap:anywhere}
.homeCategory:hover{background:rgba(63,86,104,.12);color:#3f5668;text-decoration:none}
.homeCategory:focus-visible{outline:2px solid #3f5668;outline-offset:3px}
@media(max-width:600px){.homeCategories{gap:6px;margin-bottom:14px}
.homeCategory{max-width:100%;min-height:36px}}
"""


def published_categories(posts):
    # labelColorDict contains unused repository labels; only posts define categories.
    return sorted({
        label
        for post in posts.values()
        if isinstance(post, dict) and isinstance(post.get("labels"), list)
        for label in post["labels"]
        if isinstance(label, str) and label.strip()
    })


def render_categories(html, posts):
    soup = BeautifulSoup(html, "html.parser")
    for old in soup.select(".homeCategories, style[data-card-categories]"):
        old.decompose()
    categories = published_categories(posts)
    if not categories:
        return str(soup)

    article_list = soup.select_one("#content > .SideNav")
    if article_list is None or article_list.select_one(".SideNav-item") is None:
        raise ValueError("Published posts exist but the homepage article list is missing")

    style = soup.new_tag("style", attrs={"data-card-categories": "true"})
    style.string = CATEGORY_STYLE
    soup.head.append(style)
    nav = soup.new_tag("nav", attrs={"class": "homeCategories", "aria-label": "文章分类"})
    for name in categories:
        link = soup.new_tag("a", attrs={
            "class": "homeCategory", "href": "tag.html#" + quote(name, safe="")
        })
        link.string = name
        nav.append(link)
    article_list.insert_before(nav)

    # Verify the serialized DOM, not just the source strings that create it.
    result = BeautifulSoup(str(soup), "html.parser")
    rendered_nav = result.select_one("#content > .homeCategories")
    if [link.get_text() for link in rendered_nav.select("a")] != categories:
        raise ValueError("Homepage categories do not match published article labels")
    if rendered_nav.find_next_sibling() != result.select_one("#content > .SideNav"):
        raise ValueError("Categories must be outside and immediately before the article list")
    return str(result)


def main():
    docs = Path(sys.argv[1])
    posts = json.loads((docs / "postList.json").read_text(encoding="utf-8"))
    homepage = docs / "index.html"
    rendered = render_categories(homepage.read_text(encoding="utf-8"), posts)
    homepage.write_text(rendered, encoding="utf-8")
    print("Published categories:", published_categories(posts))


if __name__ == "__main__":
    main()
