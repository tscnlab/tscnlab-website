# TSCN Lab website

Website for the Translational Sensory & Circadian Neuroscience (TSCN) lab, built with Jekyll and hosted using GitHub Pages.

## Run locally

Install Ruby and Bundler, then run:

```bash
bundle install
bundle exec jekyll serve
```

The site will be available at `http://127.0.0.1:4000/`.

For a local review that includes unpublished news drafts, run:

```bash
bash scripts/preview.sh
```

This uses project-local gems in `vendor/bundle`. Install them with
`bundle config set --local path vendor/bundle` followed by `bundle install`.
Use a current Ruby version supported by the locked Bundler version; the macOS
system Ruby is too old. Set `TSCN_RUBY_BIN` to a Ruby `bin` directory if needed.
Set `TSCN_PREVIEW_PORT` to choose another port.

News marked `published: false` appears in this preview with a draft label and
is excluded from ordinary builds. Remove that setting only after editorial
review. Website text, styles, fonts and the new resource images are local;
external tools, maps, recordings and hosted podcast media require internet access.

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

Edit `_data/podcast.yml` for the show description and platform links. The episode
catalog in `_data/podcast_episodes.json` is generated from the Light O’Clock feed.
Episode artwork and audio are served by the podcast host.

The **Sync podcast** workflow runs daily and can also be started from the
repository’s Actions tab. It commits catalog changes directly to `main` and
triggers the Pages workflow. To sync Spotify links, set `SPOTIFY_CLIENT_ID` and
`SPOTIFY_CLIENT_SECRET` as repository Actions secrets. If app ownership changes,
replace those secrets with credentials from the successor’s Spotify Developer app.

For a local check, run `python3 scripts/sync_podcast.py --dry-run`. Remove
`--dry-run` to regenerate the catalog, then run `bundle exec jekyll serve`.
Use `--feed`, `--apple`, and `--spotify` with saved responses for an offline run.

## Resources

Seminar and recorded-talk content is maintained in:

```text
_data/resources.json
```

Related images are stored in `assets/images/resources/`.

`resources/index.html` is the resources hub, and `seminar.html` links to
recordings and programmes across semesters. Past programmes are explicitly
archived, including `resources/seminars/spring-summer-2025.html` and the legacy
`seminar-20244.html` URL. Add new editions to the archive without replacing the
hub with a single semester's registration page. The LightLogR course link
points to the full course rather than a dated webinar announcement.

`software.html` includes the light-logger inventory and ENLIGHT wizard alongside
LightLogR and luox. The two new preview images come from the linked resources'
own social-preview assets. Roboto Condensed is served locally under the SIL
Open Font License in `assets/fonts/roboto-condensed/OFL.txt`.

## Deployment

The site is built with Jekyll and can be deployed through GitHub Pages.

Before deploying changes, it is useful to run:

```bash
bundle exec jekyll build
```

to check that the site builds successfully.
