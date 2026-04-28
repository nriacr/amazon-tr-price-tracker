import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


OPTIONS_PATH = Path("/data/options.json")
STATE_PATH = Path("/data/state.json")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
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
TITLE_SELECTORS = [
    "#productTitle",
    "#title",
    "meta[property='og:title']",
]
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
CARD_TITLE_SELECTORS = [
    "h2 a span",
    "h2 span",
    "a.a-link-normal h2 span",
    "[data-cy='title-recipe'] span",
    "a.a-link-normal span",
]
AMAZON_BASE_URL = "https://www.amazon.com.tr"
ASIN_URL_PATTERN = re.compile(r"/(?:dp|gp/product)/([A-Z0-9]{10})")


@dataclass
class ProductConfig:
    url: str
    target_price: Decimal
    name: Optional[str] = None


@dataclass
class SearchWatchConfig:
    search_url: str
    product_name: str
    target_price: Decimal
    name: Optional[str] = None
    max_items_to_scan: int = 24
    notify_once: bool = True


@dataclass
class SearchResultItem:
    title: str
    url: str
    price: Decimal


class TrackerError(Exception):
    pass


def log(message: str) -> None:
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        raise TrackerError(f"Fiyat ayrıştırılamadı: {raw_value!r}") from exc


def parse_bool(raw_value: Any, default: bool = False) -> bool:
    if raw_value is None:
        return default
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        return raw_value.strip().casefold() in {"1", "true", "yes", "on", "evet"}
    return bool(raw_value)


def load_config() -> Tuple[
    int, int, str, str, List[ProductConfig], List[SearchWatchConfig]
]:
    payload = load_json(OPTIONS_PATH, {})
    interval_minutes = int(payload.get("interval_minutes", 30))
    request_timeout = int(payload.get("request_timeout_seconds", 20))
    pushover_user_key = str(payload.get("pushover_user_key", "")).strip()
    pushover_api_token = str(payload.get("pushover_api_token", "")).strip()
    raw_products = payload.get("products", [])
    raw_search_watches = payload.get("search_watches", [])

    if not raw_products and not raw_search_watches:
        raise TrackerError("En az bir products veya search_watches kaydi tanimlanmali.")
    if not pushover_user_key or not pushover_api_token:
        raise TrackerError("Pushover anahtarları zorunlu.")

    products: List[ProductConfig] = []
    for item in raw_products:
        url = str(item["url"]).strip()
        target_price = parse_decimal(str(item["target_price"]))
        name = str(item["name"]).strip() if item.get("name") else None
        products.append(ProductConfig(url=url, target_price=target_price, name=name))

    search_watches: List[SearchWatchConfig] = []
    for item in raw_search_watches:
        search_url = str(item["search_url"]).strip()
        product_name = str(item["product_name"]).strip()
        target_price = parse_decimal(str(item["target_price"]))
        name = str(item["name"]).strip() if item.get("name") else None
        max_items_to_scan = int(item.get("max_items_to_scan", 24))
        notify_once = parse_bool(item.get("notify_once"), default=True)
        search_watches.append(
            SearchWatchConfig(
                search_url=search_url,
                product_name=product_name,
                target_price=target_price,
                name=name,
                max_items_to_scan=max_items_to_scan,
                notify_once=notify_once,
            )
        )

    return (
        interval_minutes,
        request_timeout,
        pushover_user_key,
        pushover_api_token,
        products,
        search_watches,
    )


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

    scripts = soup.find_all("script")
    for script in scripts:
        text = script.string or script.get_text(" ", strip=True)
        if not text:
            continue
        match = re.search(r'"price"\s*:\s*"([^"]+)"', text)
        if match:
            return parse_decimal(match.group(1))
        match = re.search(r'"priceAmount"\s*:\s*"([^"]+)"', text)
        if match:
            return parse_decimal(match.group(1))

    raise TrackerError("Sayfadan fiyat bulunamadı.")


def fetch_product(
    session: requests.Session, url: str, timeout: int
) -> Tuple[Optional[str], Decimal]:
    response = session.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()

    html = response.text
    if "captcha" in html.lower() and "robot" in html.lower():
        raise TrackerError("Amazon bot koruması nedeniyle captcha sayfası döndü.")

    soup = BeautifulSoup(html, "html.parser")
    title = extract_title(soup)
    price = extract_price(html)
    return title, price


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
    value = value.casefold()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


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


def extract_card_price(card: BeautifulSoup) -> Optional[Decimal]:
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


def extract_card_url(
    card: BeautifulSoup, fallback_asin: Optional[str] = None
) -> Optional[str]:
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
        candidate_cards = soup.select(selector)
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
        if not title or price is None or not url:
            continue
        if url in seen_urls:
            continue

        seen_urls.add(url)
        results.append(SearchResultItem(title=title, url=url, price=price))

    return results


def fetch_search_results(
    session: requests.Session, search_url: str, timeout: int, max_items_to_scan: int
) -> List[SearchResultItem]:
    response = session.get(search_url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()

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


def normalize_key(url: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", url).strip("_").lower()


def normalize_item_key(*parts: str) -> str:
    return normalize_key("_".join(parts))


def should_alert(
    state_entry: Dict[str, Any],
    current_price: Decimal,
    target_price: Decimal,
    notify_once: bool = False,
) -> bool:
    last_alerted_price = state_entry.get("last_alerted_price")
    was_below = state_entry.get("was_below_target", False)
    is_below = current_price <= target_price

    if not is_below:
        return False
    if notify_once and last_alerted_price is not None:
        return False
    if not was_below:
        return True
    if last_alerted_price is None:
        return True
    try:
        return current_price < Decimal(str(last_alerted_price))
    except InvalidOperation:
        return True


def filter_matching_results(
    results: List[SearchResultItem], product_name: str
) -> List[SearchResultItem]:
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

    state = load_json(STATE_PATH, {})
    session = requests.Session()

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
        except Exception as exc:  # noqa: BLE001
            log(f"Hata: {product.url} | {exc}")
            state[product_key] = dict(state_entry)
            state[product_key]["last_error"] = str(exc)
            state[product_key]["last_checked_at"] = utc_now()

    for watch in search_watches:
        watch_key = normalize_item_key(watch.search_url, watch.product_name)
        watch_state = state.get(watch_key, {})

        try:
            results = fetch_search_results(
                session=session,
                search_url=watch.search_url,
                timeout=request_timeout,
                max_items_to_scan=watch.max_items_to_scan,
            )
            matches = filter_matching_results(results, watch.product_name)
            display_name = watch.name or watch.product_name
            log(
                f"Arama kontrol edildi: {display_name} | eslesen_urun={len(matches)} | "
                f"hedef={watch.target_price} TL"
            )

            items_state = watch_state.get("items", {})
            notified_items = dict(watch_state.get("notified_items", {}))
            updated_items_state: Dict[str, Any] = {}
            for match in matches:
                item_key = normalize_key(match.url)
                item_state = items_state.get(item_key, {})
                already_notified = item_key in notified_items

                alert_sent = False
                if watch.notify_once and already_notified:
                    log(f"Arama bildirimi atlandi, daha once bildirildi: {match.title}")
                elif should_alert(
                    item_state,
                    match.price,
                    watch.target_price,
                    notify_once=watch.notify_once,
                ):
                    message = (
                        f"{display_name}\n"
                        f"Eslesen urun: {match.title}\n"
                        f"Guncel fiyat: {match.price} TL\n"
                        f"Hedef fiyat: {watch.target_price} TL"
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
                    notified_items[item_key] = {
                        "title": match.title,
                        "url": match.url,
                        "price": str(match.price),
                        "notified_at": utc_now(),
                    }
                    log(f"Arama bildirimi gonderildi: {match.title}")

                updated_items_state[item_key] = update_state_entry(
                    state_entry=item_state,
                    current_price=match.price,
                    target_price=watch.target_price,
                    alert_sent=alert_sent,
                )
                updated_items_state[item_key]["title"] = match.title
                updated_items_state[item_key]["url"] = match.url
                updated_items_state[item_key]["last_error"] = None

            state[watch_key] = {
                "items": updated_items_state,
                "notified_items": notified_items,
                "last_match_count": len(matches),
                "last_checked_at": utc_now(),
                "last_error": None,
            }
        except Exception as exc:  # noqa: BLE001
            log(f"Hata: {watch.search_url} | {exc}")
            state[watch_key] = dict(watch_state)
            state[watch_key]["last_error"] = str(exc)
            state[watch_key]["last_checked_at"] = utc_now()

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
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    sys.exit(main())
