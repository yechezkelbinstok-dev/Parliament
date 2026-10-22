#!/bin/sh
# Download the four Wikipedia poll articles (rendered HTML) into the given directory.
set -e
dir=${1:-wiki}
mkdir -p "$dir"
ua="Mozilla/5.0 (X11; Linux x86_64) KnessetPollChart/0.1"
for pair in \
  "Opinion_polling_for_the_2026_Israeli_legislative_election main" \
  "2025_opinion_polling_for_the_2026_Israeli_legislative_election y2025" \
  "2024_opinion_polling_for_the_2026_Israeli_legislative_election y2024" \
  "2022%E2%80%932023_opinion_polling_for_the_2026_Israeli_legislative_election y2022_23"; do
  set -- $pair
  for wait in 0 30 60 120 240; do
    sleep $wait
    code=$(curl -s -A "$ua" -o "$dir/$2.render.html" -w '%{http_code}' \
      "https://en.wikipedia.org/w/index.php?title=$1&action=render")
    [ "$code" = 200 ] && break
    echo "$2: HTTP $code, retrying" >&2
  done
  [ "$code" = 200 ] || { echo "$2: giving up" >&2; exit 1; }
done
