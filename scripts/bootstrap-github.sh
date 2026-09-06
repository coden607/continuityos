#!/usr/bin/env sh
set -eu
REPO="${1:-coden607/continuityos}"
VISIBILITY="${2:-public}"
if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required." >&2
  exit 2
fi
gh auth status >/dev/null
if ! gh repo view "$REPO" >/dev/null 2>&1; then
  gh repo create "$REPO" "--$VISIBILITY" --source . --remote origin
fi
BRANCH="$(git branch --show-current)"
git push -u origin "$BRANCH"
echo "ContinuityOS pushed to $REPO on $BRANCH"
