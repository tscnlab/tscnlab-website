# TSCN Jekyll starter

Local prototype for migrating the existing TSCN Squarespace site to Jekyll.

## Run locally

1. Install a recent Ruby and Bundler.
2. In this folder run:

```bash
bundle install
bundle exec jekyll serve
```

Then open http://127.0.0.1:4000/

If Jekyll reports a missing web server gem, run `bundle add webrick`.

## Content model

- `_posts/` = news articles
- `_members/` = team members
- `_includes/` = reusable visual components
- `_layouts/` = page shells
- `assets/css/main.css` = visual design

The sample content is intentionally incomplete. Next step: migrate actual Squarespace content/assets and tune the CSS against the current site.
