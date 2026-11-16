#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Prefer an explicitly selected Ruby, then the locally installed modern Ruby.
if [[ -n "${TSCN_RUBY_BIN:-}" ]]; then
  export PATH="$TSCN_RUBY_BIN:$PATH"
elif [[ -x "$HOME/.rubies/ruby-3.4.1/bin/ruby" ]]; then
  export PATH="$HOME/.rubies/ruby-3.4.1/bin:$PATH"
fi

export BUNDLE_USER_HOME="$PWD/.bundle"
export BUNDLE_PATH="$PWD/vendor/bundle"
export GEM_SPEC_CACHE="$PWD/vendor/gem-spec-cache"

if [[ -f vendor/bootstrap/bin/bundle ]]; then
  export GEM_HOME="$PWD/vendor/bootstrap"
  export GEM_PATH="$PWD/vendor/bootstrap"
  bundler=(ruby vendor/bootstrap/bin/bundle)
else
  bundler=(bundle)
fi

exec "${bundler[@]}" exec jekyll serve --unpublished --force_polling --host 127.0.0.1 --port "${TSCN_PREVIEW_PORT:-4000}" "$@"
