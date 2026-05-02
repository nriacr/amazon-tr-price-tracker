#!/bin/sh
python3 - <<'PY'
import json
from pathlib import Path

options_path = Path("/data/options.json")
try:
    if options_path.exists():
        payload = json.loads(options_path.read_text(encoding="utf-8"))
        changed = False
        search_pages = payload.get("search_pages") or []
        for page in search_pages:
            if not isinstance(page, dict):
                continue
            if "notify_once_in_24H" in page:
                if page.get("notify_once") != page.get("notify_once_in_24H"):
                    page["notify_once"] = page.get("notify_once_in_24H")
                    changed = True
            elif "notify_once" in page:
                page["notify_once_in_24H"] = page.get("notify_once")
                changed = True
        if changed:
            options_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
except Exception as exc:
    print(f"Config migration warning: {exc}", flush=True)
PY
python3 /app/main.py
