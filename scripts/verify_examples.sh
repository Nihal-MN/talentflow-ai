#!/bin/bash
# Upload every file in examples/ to a running TalentFlow API and print a
# compact extraction summary — a quick way to check extraction quality after
# changing the demo data (see issue #14).
#
# Usage:  scripts/verify_examples.sh [api_base_url]
# Needs:  curl + python3 + a running stack (`docker compose up -d`).
set -uo pipefail

BASE="${1:-http://localhost:8000/api/v1}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Verifying example files against $BASE"
echo

i=0
for f in "$ROOT"/examples/resumes/*.pdf "$ROOT"/examples/resumes/*.docx "$ROOT"/examples/resumes/*.txt; do
  [ -e "$f" ] || continue
  i=$((i + 1))
  curl -s -X POST "$BASE/candidates/upload" -F "file=@$f" -o "$TMP/cand_$i.json" \
    -w "resume %{http_code}  $(basename "$f")\n"
done

j=0
for f in "$ROOT"/examples/jobs/*.md; do
  [ -e "$f" ] || continue
  j=$((j + 1))
  curl -s -X POST "$BASE/jobs/upload" -F "file=@$f" -o "$TMP/job_$j.json" \
    -w "job    %{http_code}  $(basename "$f")\n"
done

echo
python3 - "$TMP" <<'PYEOF'
import json
import pathlib
import sys

tmp = pathlib.Path(sys.argv[1])

print("── candidates ─────────────────────────────────────────────")
for f in sorted(tmp.glob("cand_*.json")):
    d = json.loads(f.read_text())
    if "full_name" not in d:
        print(f"  ERROR: {d}")
        continue
    skills = ", ".join(s["name"] for s in d.get("skills", [])[:6])
    print(f"  #{d['id']:<3} {d['full_name']:<22} years={str(d.get('years_experience')):<5}"
          f" skills({len(d.get('skills', []))}): {skills}")
    for e in d.get("experiences", []):
        print(f"        · {e.get('title')} @ {e.get('company')} "
              f"({e.get('start_date')} → {e.get('end_date')})")

print()
print("── jobs ───────────────────────────────────────────────────")
for f in sorted(tmp.glob("job_*.json")):
    d = json.loads(f.read_text())
    if "title" not in d:
        print(f"  ERROR: {d}")
        continue
    skills = [r.get("normalized_skill") for r in d.get("requirements", []) if r.get("normalized_skill")]
    print(f"  #{d['id']:<3} {d['title']:<26} requirements={len(d.get('requirements', []))}"
          f" canonical_skills={skills[:8]}")
PYEOF

echo
echo "Done. (Ids and counts above are from the live API; run 'docker compose exec api python -m app.seed --reset' to restore the pristine demo dataset.)"
