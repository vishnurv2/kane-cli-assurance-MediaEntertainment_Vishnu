#!/usr/bin/env bash
# Shared helpers for the assurance pipeline.

# Run a kane-cli command, tee its NDJSON stream to a log, and return the exit
# code the CLI reported in its own `done` event rather than $?.
#
# Why: on some platforms a teardown bug collapses every shell exit code to 127.
# The Linux runner used here is not affected, but reading done.exit_code is the
# same code path people run locally on Windows, so keep them identical.
kane_run() {
  local log="$1"; shift
  local shell_code=0

  set +e
  "$@" 2>&1 | tee "$log"
  shell_code=${PIPESTATUS[0]}
  set -e

  local reported
  # -E rather than a basic-regex \+ : the escaped form relies on a GNU extension
  # that not every grep implements, and a silent non-match here would quietly
  # downgrade to the shell code the comment above exists to avoid.
  reported=$(grep -oE '"exit_code"[[:space:]]*:[[:space:]]*[0-9]+' "$log" \
    | tail -1 | grep -oE '[0-9]+$' || true)

  if [[ -n "$reported" ]]; then
    return "$reported"
  fi
  return "$shell_code"
}

# Append a heading and fenced block to the GitHub job summary.
summarize() {
  local heading="$1"; local file="$2"
  {
    echo "### ${heading}"
    echo ''
    echo '```'
    tail -c 8000 "$file" 2>/dev/null || echo '(no output)'
    echo '```'
    echo ''
  } >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
}
