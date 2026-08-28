# TSCN Lab website

Website for the Translational Sensory & Circadian Neuroscience (TSCN) lab, built with Jekyll and hosted using GitHub Pages.

## Run locally

Install Ruby and Bundler, then run:

```bash
bundle install
bundle exec jekyll serve
```

The site will be available at `http://127.0.0.1:4000/`.

If Jekyll reports a missing web server dependency:

```bash
bundle add webrick
```

## Project structure

- `_posts/` — news posts
- `_members/` — current team members
- `_alumni/` — former team members
- `_mission/` — mission statement content
- `_data/` — structured content used by pages
- `_includes/` — reusable page components
- `_layouts/` — Jekyll layouts
- `assets/css/` — stylesheets
- `assets/images/` — site images
- `assets/audio/` — podcast audio
- `scripts/` — migration and content maintenance scripts

## Adding a news post

News posts are stored in `_posts/`.

Create a Markdown file using the Jekyll naming convention:

```text
YYYY-MM-DD-post-title.md
```

Use the existing posts as a template for the front matter and content structure. Images for news posts should be added to:

```text
assets/images/news/
```

The post date determines its position in the news listing, with the newest posts shown first.

## Adding a team member

Team members are stored in `_members/`.

Create a new Markdown file for the person and use an existing member file as a template. The front matter contains the member's name, role, group and other information used by the team pages.

Member images should be added to the corresponding location under:

```text
assets/images/
```

Team members are displayed according to their group.

## Alumni

Former team members are stored in `_alumni/`. Existing alumni files can be used as templates when adding or updating entries.

## Mission statement

The mission statement is maintained in the separate TSCN Mission Statement repository and can be updated locally with:

```bash
python3 scripts/sync_mission_statement.py
```

The script updates the local content in `_mission/`.

## Podcast

Podcast content is maintained in:

```text
_data/podcast.json
```

Podcast images are stored in `assets/images/podcast/` and locally hosted audio files in `assets/audio/podcast/`.

`scripts/sync_podcast.py` was used for the original Squarespace migration and should not normally be rerun when adding or editing podcast content.

## Resources

Seminar and recorded-talk content is maintained in:

```text
_data/resources.json
```

Related images are stored in `assets/images/resources/`.

## Deployment

The site is built with Jekyll and can be deployed through GitHub Pages.

Before deploying changes, it is useful to run:

```bash
bundle exec jekyll build
```

to check that the site builds successfully.