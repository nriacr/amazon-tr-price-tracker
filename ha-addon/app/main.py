import json
import os
import random
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


OPTIONS_PATH = Path("/data/options.json")
STATE_PATH = Path("/data/state.json")
STATE_NOTIFICATION_RESET_VERSION = "1.2.0-search-alert-reset"
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"
AMAZON_BASE_URL = "https://www.amazon.com.tr"
ASIN_URL_PATTERN = re.compile(r"/(?:dp|gp/product)/([A-Z0-9]{10})")
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_DELAYS_SECONDS = [10, 30, 75]
SEARCH_PRE_DELAY_SECONDS = (5, 18)
SEARCH_HTTP_COOLDOWN_SECONDS = 45 * 60
SEARCH_ERROR_NOTIFICATION_COOLDOWN_SECONDS = 6 * 60 * 60
NOTIFY_REPEAT_SECONDS = 24 * 60 * 60
USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]
DEFAULT_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}
PRICE_META_SELECTORS = [
    ("meta", {"property": "product:price:amount"}, "content"),
    ("meta", {"itemprop": "price"}, "content"),
    ("meta", {"name": "twitter:data1"}, "content"),
]
TEXT_SELECTORS = [
    "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
    "#corePrice_feature_div .a-price .a-offscreen",
    "#tp_price_block_total_price_ww .a-offscreen",
    ".apexPriceToPay .a-offscreen",
    ".a-price.aok-align-center .a-offscreen",
    ".a-price .a-offscreen",
]
TITLE_SELECTORS = ["#productTitle", "#title", "meta[property='og:title']"]
SEARCH_CARD_SELECTORS = [
    "div[data-component-type='s-search-result']",
    "div[data-asin][data-component-type]",
    "div[data-asin]",
    ".s-result-item",
]
CARD_PRICE_SELECTORS = [
    ".a-price .a-offscreen",
    "span.a-price > span.a-offscreen",
    ".a-price-whole",
]
SECONDARY_OFFER_SELECTORS = [
    "[data-cy='secondary-offer-recipe']",
    "[data-cy='secondary-offer']",
    ".puis-secondary-offer",
    ".puis-see-details-content",
]
CARD_TITLE_SELECTORS = [
    "h2 a span",
    "h2 span",
    "a.a-link-normal h2 span",
    "[data-cy='title-recipe'] span",
    "a.a-link-normal span",
]
SEARCH_STOP_SECTION_MARKERS = (
    "yardima mi ihtiyaciniz var",
    "baktiginiz urunlere gore belirlenen urunler",
    "tarama gecmisinizdeki urunleri goruntuleyen musteriler ayrica sunlari da goruntuledi",
)
SECONDARY_OFFER_PRICE_PATTERN = re.compile(
    r"diger\s+satin\s+alma\s+secenekleri\s+"
    r"(?P<price>\d{1,3}(?:\.\d{3})*,\d{2}|\d+(?:,\d{2})?)\s*tl"
)


@dataclass
class ProductConfig:
    url: str
    target_price: Decimal
    name: Optional[str] = None


@dataclass
class SearchTargetConfig:
    name: str
    product_name: str
    target_price: Decimal


@dataclass
class SearchWatchConfig:
    name: str
    search_urls: List[str]
    targets: List[SearchTargetConfig]
    max_items_to_scan: int = 24
    notify_once_in_24h: bool = True


@dataclass
class SearchResultItem:
    title: str
    url: str
    price: Decimal


@dataclass
class SearchPriceLogRow:
    product_name: str
    price: Decimal
    target_price: Decimal


class TrackerError(Exception):
    pass


class HttpStatusTrackerError(TrackerError):
    def __init__(self, status_code: int, url: str) -> None:
        self.status_code = status_code
        super().__init__(
            f"Amazon {status_code} dondurdu; bu kontrol atlandi, sonraki turda tekrar denenecek."
        )


def log(message: str) -> None:
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def format_local_datetime(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def parse_decimal(raw_value: str) -> Decimal:
    cleaned = raw_value.strip()
    cleaned = cleaned.replace("TL", "").replace("TRY", "")
    cleaned = cleaned.replace("\xa0", "").replace(" ", "")
    cleaned = re.sub(r"[^\d,.-]", "", cleaned)

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")

    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise TrackerError(f"Fiyat ayristirilamadi: {raw_value!r}") from exc


def parse_bool(raw_value: Any, default: bool = False) -> bool:
    if raw_value is None:
        return default
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        return raw_value.strip().casefold() in {"1", "true", "yes", "on", "evet"}
    return bool(raw_value)


def parse_search_urls(item: Dict[str, Any]) -> List[str]:
    urls: List[str] = []
    for field_name in ("search_url", "search_url_2"):
        raw_url = str(item.get(field_name) or "").strip()
        if raw_url and raw_url not in urls:
            urls.append(raw_url)
    if not urls:
        raise TrackerError("search_pages icinde en az search_url doldurulmali.")
    return urls


def load_config() -> Tuple[int, int, str, str, List[ProductConfig], List[SearchWatchConfig]]:
    payload = load_json(OPTIONS_PATH, {})
    interval_minutes = int(payload.get("interval_minutes", 30))
    request_timeout = int(payload.get("request_timeout_seconds", 20))
    pushover_user_key = str(payload.get("pushover_user_key", "")).strip()
    pushover_api_token = str(payload.get("pushover_api_token", "")).strip()
    raw_products = payload.get("products", [])
    raw_search_pages = payload.get("search_pages", [])
    raw_search_targets = payload.get("search_targets", [])

    if not raw_products and not raw_search_pages:
        raise TrackerError("En az bir products veya search_pages kaydi tanimlanmali.")
    if not pushover_user_key or not pushover_api_token:
        raise TrackerError("Pushover anahtarlari zorunlu.")

    products: List[ProductConfig] = []
    for item in raw_products:
        products.append(
            ProductConfig(
                url=str(item["url"]).strip(),
                target_price=parse_decimal(str(item["target_price"])),
                name=str(item["name"]).strip() if item.get("name") else None,
            )
        )

    pages: Dict[str, SearchWatchConfig] = {}
    for item in raw_search_pages:
        page_name = str(item["name"]).strip()
        pages[page_name] = SearchWatchConfig(
            name=page_name,
            search_urls=parse_search_urls(item),
            targets=[],
            max_items_to_scan=int(item.get("max_items_to_scan", 24)),
            notify_once_in_24h=parse_bool(item.get("notify_once_in_24H"), default=True),
        )

    for item in raw_search_targets:
        search_name = str(item.get("search_name") or "").strip()
        if not search_name and len(pages) == 1:
            search_name = next(iter(pages))
        if not search_name:
            raise TrackerError(
                "Birden fazla search_pages varsa search_targets icinde search_name doldurulmali."
            )
        if search_name not in pages:
            raise TrackerError(
                f"search_targets icinde tanimlanan arama sayfasi bulunamadi: {search_name}"
            )
        target_name = str(item["name"]).strip()
        product_name = str(item.get("product_name") or target_name).strip()
        pages[search_name].targets.append(
            SearchTargetConfig(
                name=target_name,
                product_name=product_name,
                target_price=parse_decimal(str(item["target_price"])),
            )
        )

    search_watches = list(pages.values())
    if raw_search_pages and not any(watch.targets for watch in search_watches):
        raise TrackerError("En az bir search_targets kaydi tanimlanmali.")

    return (
        interval_minutes,
        request_timeout,
        pushover_user_key,
        pushover_api_token,
        products,
        search_watches,
    )


def reset_search_alert_state_once(state: Dict[str, Any]) -> Dict[str, Any]:
    meta = dict(state.get("_meta", {})) if isinstance(state.get("_meta"), dict) else {}
    if meta.get("search_alert_reset_version") == STATE_NOTIFICATION_RESET_VERSION:
        return state

    reset_count = 0
    for key, watch_state in state.items():
        if key == "_meta" or not isinstance(watch_state, dict):
            continue
        targets = watch_state.get("targets")
        if not isinstance(targets, dict):
            continue
        watch_state.pop("notified_items", None)
        for target_state in targets.values():
            if not isinstance(target_state, dict):
                continue
            items = target_state.get("items")
            if not isinstance(items, dict):
                continue
            for item_state in items.values():
                if not isinstance(item_state, dict):
                    continue
                removed_price = item_state.pop("last_alerted_price", None)
                removed_at = item_state.pop("last_alerted_at", None)
                if removed_price is not None or removed_at is not None:
                    reset_count += 1

    meta["search_alert_reset_version"] = STATE_NOTIFICATION_RESET_VERSION
    meta["search_alert_reset_at"] = utc_now()
    state["_meta"] = meta
    log(f"Arama bildirim susturma kayitlari sifirlandi: {reset_count} urun")
    return state


def build_headers() -> Dict[str, str]:
    headers = dict(DEFAULT_HEADERS)
    headers["User-Agent"] = random.choice(USER_AGENTS)
    headers["Referer"] = AMAZON_BASE_URL + "/"
    return headers


def fetch_with_retries(session: requests.Session, url: str, timeout: int) -> requests.Response:
    last_status: Optional[int] = None
    attempts = len(RETRY_DELAYS_SECONDS) + 1

    for attempt in range(attempts):
        response = session.get(url, headers=build_headers(), timeout=timeout)
        if response.status_code not in RETRY_STATUS_CODES:
            response.raise_for_status()
            return response

        last_status = response.status_code
        if attempt < len(RETRY_DELAYS_SECONDS):
            delay = RETRY_DELAYS_SECONDS[attempt]
            log(
                f"Amazon gecici hata verdi ({response.status_code}); "
                f"{delay} saniye sonra tekrar denenecek."
            )
            time.sleep(delay)

    raise HttpStatusTrackerError(last_status or 0, url)


def extract_title(soup: BeautifulSoup) -> Optional[str]:
    for selector in TITLE_SELECTORS:
        element = soup.select_one(selector)
        if not element:
            continue
        if element.name == "meta":
            content = element.get("content", "").strip()
            if content:
                return content
        text = element.get_text(" ", strip=True)
        if text:
            return text
    return None


def extract_price(html: str) -> Decimal:
    soup = BeautifulSoup(html, "html.parser")

    for tag_name, attrs, attr_name in PRICE_META_SELECTORS:
        element = soup.find(tag_name, attrs=attrs)
        if element and element.get(attr_name):
            return parse_decimal(str(element[attr_name]))

    for selector in TEXT_SELECTORS:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(" ", strip=True)
            if text:
                return parse_decimal(text)

    for script in soup.find_all("script"):
        text = script.string or script.get_text(" ", strip=True)
        if not text:
            continue
        match = re.search(r'"price"\s*:\s*"([^"]+)"', text)
        if match:
            return parse_decimal(match.group(1))
        match = re.search(r'"priceAmount"\s*:\s*"([^"]+)"', text)
        if match:
            return parse_decimal(match.group(1))

    raise TrackerError("Sayfadan fiyat bulunamadi.")


def fetch_product(session: requests.Session, url: str, timeout: int) -> Tuple[Optional[str], Decimal]:
    response = fetch_with_retries(session, url, timeout)
    html = response.text
    if "captcha" in html.lower() and "robot" in html.lower():
        raise TrackerError("Amazon bot korumasi nedeniyle captcha sayfasi dondu.")

    soup = BeautifulSoup(html, "html.parser")
    return extract_title(soup), extract_price(html)


def make_absolute_url(raw_url: str) -> str:
    if raw_url.startswith("http://") or raw_url.startswith("https://"):
        return raw_url
    if raw_url.startswith("/"):
        return f"{AMAZON_BASE_URL}{raw_url}"
    return f"{AMAZON_BASE_URL}/{raw_url}"


def extract_asin_from_url(url: str) -> Optional[str]:
    match = ASIN_URL_PATTERN.search(url)
    if not match:
        return None
    return match.group(1)


def canonical_product_url(raw_url: str, fallback_asin: Optional[str] = None) -> str:
    absolute_url = make_absolute_url(raw_url)
    asin = extract_asin_from_url(absolute_url) or fallback_asin
    if asin:
        return f"{AMAZON_BASE_URL}/dp/{asin}"
    return absolute_url.split("?", 1)[0]


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def normalize_offer_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.replace("ı", "i")
    return re.sub(r"\s+", " ", normalized).strip()


def is_search_stop_section_text(value: str) -> bool:
    normalized = normalize_offer_text(value)
    return any(marker in normalized for marker in SEARCH_STOP_SECTION_MARKERS)


def find_search_stop_marker(soup: BeautifulSoup) -> Optional[Any]:
    for text_node in soup.find_all(string=True):
        if is_search_stop_section_text(str(text_node)):
            return text_node
    return None


def filter_cards_before_stop_sections(cards: List[Any], soup: BeautifulSoup) -> List[Any]:
    marker = find_search_stop_marker(soup)
    if marker is None:
        return cards

    after_marker_ids = {
        id(element)
        for element in marker.next_elements
        if getattr(element, "name", None)
    }
    return [card for card in cards if id(card) not in after_marker_ids]


def normalize_key(url: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", url).strip("_").lower()


def normalize_item_key(*parts: str) -> str:
    return normalize_key("_".join(parts))


def format_tl(value: Decimal) -> str:
    formatted = f"{value:,.2f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def format_signed_tl(value: Decimal) -> str:
    sign = "+" if value >= 0 else "-"
    return f"{sign}{format_tl(abs(value))}"


def shorten_log_text(value: str, max_length: int = 90) -> str:
    clean = re.sub(r"\s+", " ", value).strip()
    if len(clean) <= max_length:
        return clean
    return clean[: max_length - 3].rstrip() + "..."


def log_cell(value: str, width: int, align: str = "left") -> str:
    text = shorten_log_text(value, width)
    if align == "right":
        return text.rjust(width)
    return text.ljust(width)


def log_search_price_summary(rows: List[SearchPriceLogRow]) -> None:
    if not rows:
        log("Ozet: eslesen=0")
        return

    rows.sort(key=lambda row: (normalize_text(row.product_name), row.price))
    no_width = 3
    product_width = 36
    price_width = 10

    header = (
        f"{'No':>{no_width}} | "
        f"{log_cell('Ürün Adı', product_width)} | "
        f"{'Fiyat':>{price_width}} | "
        f"{'Hedef':>{price_width}} | "
        f"{'Fark':>{price_width}}"
    )
    separator = (
        f"{'-' * no_width}-+-"
        f"{'-' * product_width}-+-"
        f"{'-' * price_width}-+-"
        f"{'-' * price_width}-+-"
        f"{'-' * price_width}"
    )

    log(f"Ozet: eslesen={len(rows)}")
    log(header)
    log(separator)
    for index, row in enumerate(rows, start=1):
        difference = row.price - row.target_price
        log(
            f"{index:>{no_width}} | "
            f"{log_cell(row.product_name, product_width)} | "
            f"{format_tl(row.price):>{price_width}} | "
            f"{format_tl(row.target_price):>{price_width}} | "
            f"{format_signed_tl(difference):>{price_width}}"
        )


def extract_card_title(card: BeautifulSoup) -> Optional[str]:
    for selector in CARD_TITLE_SELECTORS:
        element = card.select_one(selector)
        if not element:
            continue
        text = element.get_text(" ", strip=True)
        if text:
            return text

    for attr_name in ("aria-label", "title", "alt"):
        element = card.find(attrs={attr_name: True})
        if element:
            text = str(element.get(attr_name, "")).strip()
            if text:
                return text
    return None


def extract_price_after_secondary_offer_text(text: str) -> Optional[Decimal]:
    normalized = normalize_offer_text(text)
    if "diger satin alma secenekleri" not in normalized or "ikinci el" not in normalized:
        return None

    match = SECONDARY_OFFER_PRICE_PATTERN.search(normalized)
    if not match:
        return None

    try:
        return parse_decimal(match.group("price"))
    except TrackerError:
        return None


def extract_secondary_offer_price(card: BeautifulSoup) -> Optional[Decimal]:
    for selector in SECONDARY_OFFER_SELECTORS:
        for element in card.select(selector):
            price = extract_price_after_secondary_offer_text(element.get_text(" ", strip=True))
            if price is not None:
                return price

    return extract_price_after_secondary_offer_text(card.get_text(" ", strip=True))


def extract_card_price(card: BeautifulSoup) -> Optional[Decimal]:
    secondary_offer_price = extract_secondary_offer_price(card)
    if secondary_offer_price is not None:
        return secondary_offer_price

    for selector in CARD_PRICE_SELECTORS:
        element = card.select_one(selector)
        if not element:
            continue
        text = element.get_text(" ", strip=True)
        if text:
            try:
                return parse_decimal(text)
            except TrackerError:
                continue

    full_text = card.get_text(" ", strip=True)
    match = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*TL", full_text)
    if match:
        return parse_decimal(match.group(1))
    match = re.search(r"(\d+(?:,\d{2})?)\s*TL", full_text)
    if match:
        return parse_decimal(match.group(1))
    return None


def extract_card_url(card: BeautifulSoup, fallback_asin: Optional[str] = None) -> Optional[str]:
    link = (
        card.select_one("h2 a[href]")
        or card.select_one("a[href*='/dp/']")
        or card.select_one("a[href*='/gp/product/']")
        or card.select_one("a[href]")
    )
    if not link:
        return None
    href = str(link.get("href", "")).strip()
    if not href:
        return None
    return canonical_product_url(href, fallback_asin)


def extract_search_results(html: str, max_items_to_scan: int) -> List[SearchResultItem]:
    soup = BeautifulSoup(html, "html.parser")
    cards: List[Any] = []
    for selector in SEARCH_CARD_SELECTORS:
        candidate_cards = filter_cards_before_stop_sections(soup.select(selector), soup)
        if candidate_cards:
            cards = candidate_cards
            break

    results: List[SearchResultItem] = []
    seen_urls = set()
    for card in cards:
        asin = str(card.get("data-asin", "")).strip() or None
        if card.name == "div" and card.has_attr("data-asin") and not asin:
            continue
        if len(results) >= max_items_to_scan:
            break

        title = extract_card_title(card)
        price = extract_card_price(card)
        url = extract_card_url(card, asin)
        if not title or price is None or not url or url in seen_urls:
            continue

        seen_urls.add(url)
        results.append(SearchResultItem(title=title, url=url, price=price))

    return results


def dedupe_search_results(results: List[SearchResultItem]) -> List[SearchResultItem]:
    deduped: Dict[str, SearchResultItem] = {}
    for item in results:
        existing = deduped.get(item.url)
        if existing is None or item.price < existing.price:
            deduped[item.url] = item
    return list(deduped.values())


def fetch_search_results(
    session: requests.Session, search_url: str, timeout: int, max_items_to_scan: int
) -> List[SearchResultItem]:
    delay = random.randint(*SEARCH_PRE_DELAY_SECONDS)
    log(f"Arama istegi oncesi {delay} saniye bekleniyor.")
    time.sleep(delay)

    response = fetch_with_retries(session, search_url, timeout)
    html = response.text
    if "captcha" in html.lower() and "robot" in html.lower():
        raise TrackerError("Amazon bot korumasi nedeniyle captcha sayfasi dondu.")

    results = extract_search_results(html, max_items_to_scan)
    if not results:
        raise TrackerError("Arama sonuc sayfasinda okunabilir urun bulunamadi.")
    return results


def send_pushover(
    session: requests.Session,
    user_key: str,
    api_token: str,
    title: str,
    message: str,
    url: str,
    timeout: int,
) -> None:
    response = session.post(
        PUSHOVER_URL,
        data={
            "token": api_token,
            "user": user_key,
            "title": title,
            "message": message,
            "url": url,
            "url_title": "Amazon'da ac",
        },
        timeout=timeout,
    )
    response.raise_for_status()


def should_alert(
    state_entry: Dict[str, Any],
    current_price: Decimal,
    target_price: Decimal,
    repeat_after_24h: bool = False,
) -> bool:
    if current_price > target_price:
        return False

    last_alerted_price = state_entry.get("last_alerted_price")
    if last_alerted_price is None:
        return True

    try:
        if current_price < Decimal(str(last_alerted_price)):
            return True
    except InvalidOperation:
        return True

    if repeat_after_24h:
        last_alerted_at = parse_iso_datetime(state_entry.get("last_alerted_at"))
        if not last_alerted_at:
            return False
        elapsed = (datetime.now(timezone.utc) - last_alerted_at).total_seconds()
        return elapsed >= NOTIFY_REPEAT_SECONDS

    return not state_entry.get("was_below_target", False)


def should_send_error_notification(
    state_entry: Dict[str, Any], error_message: str, error_status: Optional[int]
) -> bool:
    signature = f"{error_status or 'error'}:{error_message}"
    if state_entry.get("last_error_notification_signature") != signature:
        return True

    last_notified = parse_iso_datetime(state_entry.get("last_error_notified_at"))
    if not last_notified:
        return True

    elapsed = (datetime.now(timezone.utc) - last_notified).total_seconds()
    return elapsed >= SEARCH_ERROR_NOTIFICATION_COOLDOWN_SECONDS


def update_error_notification_state(
    state_entry: Dict[str, Any], error_message: str, error_status: Optional[int]
) -> Dict[str, Any]:
    updated = dict(state_entry)
    updated["last_error_notified_at"] = utc_now()
    updated["last_error_notification_signature"] = f"{error_status or 'error'}:{error_message}"
    return updated


def filter_matching_results(results: List[SearchResultItem], product_name: str) -> List[SearchResultItem]:
    needle = normalize_text(product_name)
    return [item for item in results if needle in normalize_text(item.title)]


def update_state_entry(
    state_entry: Dict[str, Any],
    current_price: Decimal,
    target_price: Decimal,
    alert_sent: bool,
) -> Dict[str, Any]:
    updated = dict(state_entry)
    updated["last_price"] = str(current_price)
    updated["last_checked_at"] = utc_now()
    updated["was_below_target"] = current_price <= target_price
    if alert_sent:
        updated["last_alerted_price"] = str(current_price)
        updated["last_alerted_at"] = utc_now()
    return updated


def cooldown_remaining_seconds(watch_state: Dict[str, Any]) -> int:
    status = watch_state.get("last_error_status")
    if status not in {429, 503}:
        return 0

    last_checked = parse_iso_datetime(watch_state.get("last_checked_at"))
    if not last_checked:
        return 0

    elapsed = (datetime.now(timezone.utc) - last_checked).total_seconds()
    remaining = SEARCH_HTTP_COOLDOWN_SECONDS - int(elapsed)
    return max(0, remaining)


def check_products_once() -> None:
    (
        interval_minutes,
        request_timeout,
        user_key,
        api_token,
        products,
        search_watches,
    ) = load_config()
    _ = interval_minutes

    state = reset_search_alert_state_once(load_json(STATE_PATH, {}))
    session = requests.Session()
    search_price_log_rows: List[SearchPriceLogRow] = []

    for product in products:
        product_key = normalize_key(product.url)
        state_entry = state.get(product_key, {})

        try:
            title, current_price = fetch_product(session, product.url, request_timeout)
            display_name = product.name or title or product.url
            log(
                f"Kontrol edildi: {display_name} | fiyat={current_price} TL | "
                f"hedef={product.target_price} TL"
            )

            alert_sent = False
            if should_alert(state_entry, current_price, product.target_price):
                message = (
                    f"{display_name}\n"
                    f"Guncel fiyat: {current_price} TL\n"
                    f"Hedef fiyat: {product.target_price} TL"
                )
                send_pushover(
                    session=session,
                    user_key=user_key,
                    api_token=api_token,
                    title="Amazon fiyat alarmi",
                    message=message,
                    url=product.url,
                    timeout=request_timeout,
                )
                alert_sent = True
                log(f"Bildirim gonderildi: {display_name}")

            state[product_key] = update_state_entry(
                state_entry=state_entry,
                current_price=current_price,
                target_price=product.target_price,
                alert_sent=alert_sent,
            )
            state[product_key]["last_error"] = None
            state[product_key]["last_error_status"] = None
        except Exception as exc:  # noqa: BLE001
            log(f"Hata: {product.url} | {exc}")
            state[product_key] = dict(state_entry)
            state[product_key]["last_error"] = str(exc)
            state[product_key]["last_error_status"] = getattr(exc, "status_code", None)
            state[product_key]["last_checked_at"] = utc_now()

    for watch in search_watches:
        if not watch.targets:
            log(f"Arama atlandi: {watch.name} | Bu arama sayfasina hedef urun eklenmemis.")
            continue

        watch_key = normalize_item_key(watch.name, *watch.search_urls)
        watch_state = state.get(watch_key, {})
        remaining = cooldown_remaining_seconds(watch_state)
        if remaining > 0:
            minutes = max(1, round(remaining / 60))
            log(
                f"Arama gecici olarak atlandi: {watch.name} | "
                f"Amazon korumasi sonrasi {minutes} dk sonra yeniden denenecek."
            )
            skipped_state = dict(watch_state)
            skipped_state["last_skipped_at"] = utc_now()
            state[watch_key] = skipped_state
            continue

        try:
            all_results: List[SearchResultItem] = []
            failed_urls: List[str] = []
            for index, search_url in enumerate(watch.search_urls, start=1):
                try:
                    url_results = fetch_search_results(
                        session=session,
                        search_url=search_url,
                        timeout=request_timeout,
                        max_items_to_scan=watch.max_items_to_scan,
                    )
                    all_results.extend(url_results)
                    log(
                        f"Arama linki kontrol edildi: {watch.name} | "
                        f"link={index}/{len(watch.search_urls)} | okunan_urun={len(url_results)}"
                    )
                except Exception as exc:  # noqa: BLE001
                    failed_urls.append(f"{search_url} | {exc}")
                    log(f"Arama linki hatasi: {watch.name} | link={index}/{len(watch.search_urls)} | {exc}")

            if not all_results:
                raise TrackerError("Arama sayfasindaki linklerin hicbirinde okunabilir urun bulunamadi.")

            results = dedupe_search_results(all_results)
            if failed_urls:
                log(
                    f"Arama kismen kontrol edildi: {watch.name} | "
                    f"basarili_link={len(watch.search_urls) - len(failed_urls)} | hatali_link={len(failed_urls)}"
                )
            log(
                f"Arama sayfasi kontrol edildi: {watch.name} | "
                f"okunan_urun={len(results)} | link_sayisi={len(watch.search_urls)} | "
                f"hedef_sayisi={len(watch.targets)}"
            )

            targets_state = dict(watch_state.get("targets", {}))
            for target in watch.targets:
                target_key = normalize_key(target.name)
                target_state = targets_state.get(target_key, {})
                items_state = target_state.get("items", {})
                updated_items_state: Dict[str, Any] = dict(items_state)
                matches = filter_matching_results(results, target.product_name)

                log(
                    f"Arama hedefi kontrol edildi: {watch.name} / {target.name} | "
                    f"eslesen_urun={len(matches)} | hedef={target.target_price} TL"
                )

                for match in matches:
                    search_price_log_rows.append(
                        SearchPriceLogRow(
                            product_name=target.product_name,
                            price=match.price,
                            target_price=target.target_price,
                        )
                    )
                    item_key = normalize_key(match.url)
                    item_state = dict(items_state.get(item_key, {}))
                    alert_sent = False

                    if should_alert(
                        item_state,
                        match.price,
                        target.target_price,
                        repeat_after_24h=watch.notify_once_in_24h,
                    ):
                        message = (
                            f"Arama: {watch.name}\n"
                            f"Hedef: {target.name}\n"
                            f"Eslesen urun: {match.title}\n"
                            f"Guncel fiyat: {match.price} TL\n"
                            f"Hedef fiyat: {target.target_price} TL"
                        )
                        send_pushover(
                            session=session,
                            user_key=user_key,
                            api_token=api_token,
                            title="Amazon arama alarmi",
                            message=message,
                            url=match.url,
                            timeout=request_timeout,
                        )
                        alert_sent = True
                        log(f"Arama bildirimi gonderildi: {target.name} | {match.title}")
                    elif match.price <= target.target_price and watch.notify_once_in_24h:
                        log(
                            f"Arama bildirimi atlandi, 24 saat dolmadi veya fiyat daha dusuk degil: "
                            f"{match.title} | fiyat={match.price} TL"
                        )

                    updated_items_state[item_key] = update_state_entry(
                        state_entry=item_state,
                        current_price=match.price,
                        target_price=target.target_price,
                        alert_sent=alert_sent,
                    )
                    updated_items_state[item_key]["title"] = match.title
                    updated_items_state[item_key]["url"] = match.url
                    updated_items_state[item_key]["last_error"] = None

                targets_state[target_key] = {
                    "items": updated_items_state,
                    "last_match_count": len(matches),
                    "last_checked_at": utc_now(),
                }

            state[watch_key] = {
                "targets": targets_state,
                "last_checked_at": utc_now(),
                "last_error": None if not failed_urls else "; ".join(failed_urls)[:900],
                "last_error_status": None,
                "last_error_notified_at": watch_state.get("last_error_notified_at"),
                "last_error_notification_signature": watch_state.get(
                    "last_error_notification_signature"
                ),
            }
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)
            error_status = getattr(exc, "status_code", None)
            log(f"Hata: {' | '.join(watch.search_urls)} | {error_message}")

            updated_watch_state = dict(watch_state)
            if should_send_error_notification(updated_watch_state, error_message, error_status):
                try:
                    target_names = ", ".join(target.name for target in watch.targets)
                    message = (
                        f"Arama: {watch.name}\n"
                        f"Hedefler: {target_names}\n"
                        f"Hata: {error_message}\n"
                        f"Kontrol etmen gerekebilir: link gecersiz olabilir, Amazon korumasi olabilir veya sayfa yapisi degismis olabilir."
                    )
                    send_pushover(
                        session=session,
                        user_key=user_key,
                        api_token=api_token,
                        title="Amazon arama hatasi",
                        message=message[:900],
                        url=watch.search_urls[0],
                        timeout=request_timeout,
                    )
                    updated_watch_state = update_error_notification_state(
                        updated_watch_state, error_message, error_status
                    )
                    log(f"Arama hata bildirimi gonderildi: {watch.name}")
                except Exception as notify_exc:  # noqa: BLE001
                    log(f"Arama hata bildirimi gonderilemedi: {watch.name} | {notify_exc}")

            updated_watch_state["last_error"] = error_message
            updated_watch_state["last_error_status"] = error_status
            updated_watch_state["last_checked_at"] = utc_now()
            state[watch_key] = updated_watch_state

    if search_watches:
        log_search_price_summary(search_price_log_rows)
    save_json(STATE_PATH, state)


def main() -> int:
    try:
        interval_minutes, _, _, _, _, _ = load_config()
    except Exception as exc:  # noqa: BLE001
        log(f"Baslatma hatasi: {exc}")
        return 1

    run_once = os.getenv("RUN_ONCE", "").strip() == "1"
    if run_once:
        check_products_once()
        return 0

    log(f"Servis basladi. Kontrol araligi: {interval_minutes} dakika")
    while True:
        check_products_once()
        next_check = datetime.now().astimezone() + timedelta(minutes=interval_minutes)
        log(f"Sonraki kontrol: {format_local_datetime(next_check)}")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    sys.exit(main())
