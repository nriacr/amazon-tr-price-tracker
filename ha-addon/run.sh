#!/bin/sh
set -eu

python3 - <<'PY' &
import json
import os
from datetime import datetime, timedelta
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

OPTIONS_PATH = Path('/data/options.json')
STATE_PATH = Path('/data/state.json')
WEB_PORT = 8099
ADDON_SLUG = 'amazon_tr_price_tracker'


def load_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        with path.open('r', encoding='utf-8') as file:
            return json.load(file)
    except Exception:
        return default


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed.astimezone() if parsed.tzinfo else parsed


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return '-'
    return value.strftime('%Y-%m-%d %H:%M:%S')


def addon_id_candidates() -> list[str]:
    candidates: list[str] = []
    hostname = os.getenv('HOSTNAME', '').strip()
    if hostname:
        candidates.append(hostname.replace('-', '_'))
    candidates.extend([ADDON_SLUG, f'local_{ADDON_SLUG}'])

    unique_candidates: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in unique_candidates:
            unique_candidates.append(candidate)
    return unique_candidates


def collect_summary() -> dict[str, Any]:
    options = load_json(OPTIONS_PATH, {})
    state = load_json(STATE_PATH, {})
    products = options.get('products') if isinstance(options.get('products'), list) else []
    search_pages = options.get('search_pages') if isinstance(options.get('search_pages'), list) else []
    search_targets = options.get('search_targets') if isinstance(options.get('search_targets'), list) else []
    error_cutoff = datetime.now().astimezone() - timedelta(hours=24)

    last_checks = []
    error_count = 0
    if isinstance(state, dict):
        for key, value in state.items():
            if key == '_meta' or not isinstance(value, dict):
                continue
            checked_at = parse_datetime(value.get('last_checked_at'))
            if checked_at:
                last_checks.append(checked_at)
            if value.get('last_error') and checked_at and checked_at >= error_cutoff:
                error_count += 1
            targets = value.get('targets')
            if isinstance(targets, dict):
                for target_state in targets.values():
                    if not isinstance(target_state, dict):
                        continue
                    checked_at = parse_datetime(target_state.get('last_checked_at'))
                    if checked_at:
                        last_checks.append(checked_at)

    return {
        'interval': options.get('interval_minutes', '-'),
        'products': len(products),
        'search_pages': len(search_pages),
        'search_targets': len(search_targets),
        'last_check': format_datetime(max(last_checks) if last_checks else None),
        'errors': error_count,
        'configured': bool(options),
    }


def render_page() -> bytes:
    summary = collect_summary()
    status = 'Çalışıyor' if summary['configured'] else 'Ayar bekliyor'
    status_class = 'status-ok' if summary['configured'] else 'status-warn'
    error_class = 'status-error' if int(summary['errors']) > 0 else ''
    log_url = f"/hassio/addon/{addon_id_candidates()[0]}/logs"
    config_url = f"/hassio/addon/{addon_id_candidates()[0]}/config"
    cards = [
        ('Durum', status, status_class),
        ('Kontrol aralığı', f"{summary['interval']} dakika", ''),
        ('Ürün linkleri', summary['products'], ''),
        ('Arama sayfaları', summary['search_pages'], ''),
        ('Arama hedefleri', summary['search_targets'], ''),
        ('Son kontrol', summary['last_check'], ''),
        ('Hata sayısı', summary['errors'], error_class),
    ]
    card_html = ''.join(
        f"<section class='card {escape(str(css_class))}'><span>{escape(str(label))}</span><strong>{escape(str(value))}</strong></section>"
        for label, value, css_class in cards
    )
    html = f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="60">
  <title>Amazon Türkiye Fiyat Takibi</title>
  <style>
    :root {{ color-scheme: dark; --bg:#121212; --panel:#1f1f1f; --line:#333; --text:#f1f1f1; --muted:#aaa; --accent:#ff9900; --accent2:#f6c453; --ok:#4ade80; --warn:#facc15; --bad:#fb7185; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: radial-gradient(circle at top left, #2b2112, var(--bg) 42%); color:var(--text); }}
    main {{ max-width: 920px; margin: 0 auto; padding: 28px 18px 44px; }}
    .hero {{ border:1px solid var(--line); border-radius:22px; padding:24px; background:rgba(31,31,31,.86); box-shadow:0 22px 60px rgba(0,0,0,.28); }}
    h1 {{ margin:0 0 8px; font-size: clamp(28px, 5vw, 44px); letter-spacing:-.04em; }}
    p {{ margin:0; color:var(--muted); line-height:1.55; }}
    .badge {{ display:inline-flex; gap:8px; align-items:center; margin-bottom:18px; color:#171717; background:var(--accent); border-radius:999px; padding:8px 13px; font-weight:700; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:20px; }}
    .button {{ display:inline-flex; align-items:center; justify-content:center; min-height:44px; padding:0 16px; border-radius:14px; border:1px solid transparent; text-decoration:none; font-weight:800; }}
    .button.primary {{ color:#161616; background:linear-gradient(135deg, var(--accent), var(--accent2)); }}
    .button.secondary {{ color:var(--text); background:#202020; border-color:var(--line); }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin-top:18px; }}
    .card {{ border:1px solid var(--line); border-radius:16px; padding:16px; background:#181818; min-height:92px; }}
    .card span {{ display:block; color:var(--muted); font-size:13px; margin-bottom:10px; }}
    .card strong {{ display:block; font-size:22px; line-height:1.2; overflow-wrap:anywhere; }}
    .card.status-ok {{ border-color:rgba(74,222,128,.45); background:linear-gradient(135deg, rgba(74,222,128,.13), #181818 58%); }}
    .card.status-ok strong {{ color:var(--ok); }}
    .card.status-warn {{ border-color:rgba(250,204,21,.45); background:linear-gradient(135deg, rgba(250,204,21,.12), #181818 58%); }}
    .card.status-warn strong {{ color:var(--warn); }}
    .card.status-error {{ border-color:rgba(251,113,133,.5); background:linear-gradient(135deg, rgba(251,113,133,.13), #181818 58%); }}
    .card.status-error strong {{ color:var(--bad); }}
    .note {{ margin-top:18px; border-left:4px solid var(--accent); padding:12px 14px; background:rgba(255,153,0,.1); border-radius:10px; }}
    .footer {{ margin-top:18px; font-size:13px; color:var(--muted); }}
  </style>
</head>
<body>
  <main>
    <div class="hero">
      <div class="badge">Amazon Türkiye alarmı</div>
      <h1>Amazon Türkiye Fiyat Takibi</h1>
      <p>Bu sayfa Home Assistant kenar çubuğu için kısa durum ekranıdır. Fiyat takibi arka planda çalışmaya devam eder.</p>
      <div class="actions">
        <a class="button primary" href="{escape(log_url)}" target="_top">Kayıtları Aç</a>
        <a class="button secondary" href="{escape(config_url)}" target="_top">Ayarları Aç</a>
      </div>
      <div class="grid">{card_html}</div>
      <p class="note">Kayıt ve ayar butonları Home Assistant add-on sayfasındaki ilgili sekmeleri açar. Hata sayısı yalnızca son 24 saati kapsar.</p>
      <p class="footer">Sayfa 60 saniyede bir otomatik yenilenir.</p>
    </div>
  </main>
</body>
</html>"""
    return html.encode('utf-8')


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.rstrip('/') == '/health':
            payload = b'ok\n'
            content_type = 'text/plain; charset=utf-8'
        else:
            payload = render_page()
            content_type = 'text/html; charset=utf-8'
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        return


ThreadingHTTPServer(('0.0.0.0', WEB_PORT), StatusHandler).serve_forever()
PY

exec python3 /app/main.py
