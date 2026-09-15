#!/usr/bin/env bash
# Drives the demo in DEMO.md, pausing between beats so you can talk.
#
#   ./scripts/demo.sh            full run: ingest, extract, checkpoint, graph
#   ./scripts/demo.sh --walk     no service calls, walk an existing graph
#
# Run from the repo root. Ctrl-C is safe at any pause.

set -u
cd "$(dirname "$0")/.." || exit 1

WALK=0
[ "${1:-}" = "--walk" ] && WALK=1

bold=$(tput bold 2>/dev/null || true)
dim=$(tput dim 2>/dev/null || true)
off=$(tput sgr0 2>/dev/null || true)

beat() {
  echo
  echo "${bold}── $1${off}"
  [ -n "${2:-}" ] && echo "${dim}   $2${off}"
  echo "${dim}   [enter to run]${off}"
  read -r _
}

say() { echo "${dim}   $1${off}"; }

# ---------------------------------------------------------------- preflight

if ! kane-cli whoami >/dev/null 2>&1; then
  echo "not authenticated - run: kane-cli login --username <user> --access-key <key>"
  exit 1
fi

if ! curl -sf http://127.0.0.1:8080 >/dev/null 2>&1; then
  echo "starting the app on :8080"
  python3 -m http.server 8080 --directory app >/dev/null 2>&1 &
  APP_PID=$!
  trap 'kill $APP_PID 2>/dev/null' EXIT
  for _ in $(seq 1 20); do curl -sf http://127.0.0.1:8080 >/dev/null && break; sleep 1; done
fi
kane-cli config set-url http://127.0.0.1:8080 >/dev/null 2>&1

echo "${bold}StreamRights · assurance demo${off}"
say "app on http://127.0.0.1:8080 · authenticated"
say "the payload is FINDINGS.md F1 - read it before you run this"

# ------------------------------------------------------------------- beats

if [ "$WALK" -eq 0 ]; then
  beat "1 · Ingest both sources" "local, free - lands the documents"
  kane-cli context ingest sources/prd-entitlement-playback.md \
    sources/rights-schedule-2026.md --mode ci

  beat "2 · Extract use-cases" "the rights schedule will fail - say why, out loud (FINDINGS.md F2)"
  kane-cli context extract --mode ci
  echo
  say "^ if you saw CRITERIA_OPS_UNSUPPORTED, that is the extract@5 binding."
  say "  name it before they find it."
fi

beat "3 · The graph" "every node cites the line it came from"
kane-cli context list --json --type usecase 2>/dev/null | head -6
echo
kane-cli context list 2>/dev/null | tail -20

beat "4 · Lineage for one node" "no model call - replays what it recorded"
FIRST_UC=$(kane-cli context list --json --type usecase 2>/dev/null \
             | python3 scripts/refs.py uc- | awk '{print $1}')
if [ -n "$FIRST_UC" ]; then
  kane-cli context explain "$FIRST_UC" 2>/dev/null | head -30
else
  say "no use-cases in the graph - run without --walk first"
fi

beat "5 · The finding" "THIS IS THE DEMO - slow down, read all three aloud"
echo
echo "   R1  sources/prd-entitlement-playback.md:19"
sed -n '19,23p' sources/prd-entitlement-playback.md | sed 's/^/      /'
echo
echo "   R2  sources/prd-entitlement-playback.md:25"
sed -n '25,29p' sources/prd-entitlement-playback.md | sed 's/^/      /'
echo
echo "   R4  sources/prd-entitlement-playback.md:37"
sed -n '37,41p' sources/prd-entitlement-playback.md | sed 's/^/      /'
echo
say "ask: R1 hides the title, R2 says browse is the only route to a detail"
say "page - so how does a viewer ever reach the page where R4 happens?"
say "then WAIT. do not fill the silence."

beat "6 · The dead branch" "app/app.js:182 - R4 implemented correctly, unreachable"
sed -n '182,189p' app/app.js | sed 's/^/   /'
echo
say "no test written from R4 would have told you - the test passes or fails"
say "on a page that was never reachable."

beat "7 · Coverage, honestly" "own the zero, do not skip past it"
kane-cli cover gaps 2>/dev/null || say "(no evidence pack yet - proven axis empty)"
echo
say "read the '0 failing' out loud - it is the number that matters."
say "the gap between designed and proven is blocked/not-run, i.e. the"
say "executor stalling (FINDINGS.md F3), NOT the product failing."

beat "8 · Hand over the link" "renders the graph you send after the call"
mkdir -p site
if kane-cli context view --out site/index.html --no-open 2>/dev/null; then
  say "wrote site/index.html ($(wc -c < site/index.html | tr -d ' ') bytes)"
  command -v open >/dev/null && open site/index.html
else
  say "context view produced nothing - check the graph is populated"
fi

echo
echo "${bold}Close on:${off}"
echo "   \"The tool did not find bugs in the product. It found a requirement"
echo "    that could never be satisfied, and it found it before anyone wrote code.\""
echo
say "questions you will get - and what not to claim - are in DEMO.md"
