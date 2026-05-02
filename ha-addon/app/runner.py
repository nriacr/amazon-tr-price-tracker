import re
import sys

import main as tracker


def shorten_log_text(value: str, max_length: int) -> str:
    clean = re.sub(r"\s+", " ", value).strip()
    if len(clean) <= max_length:
        return clean
    return clean[: max_length - 3].rstrip() + "..."


def log_cell(value: str, width: int) -> str:
    return shorten_log_text(value, width).ljust(width)


def log_search_price_summary(rows):
    if not rows:
        tracker.log("Ozet: eslesen=0")
        return

    rows.sort(key=lambda row: (tracker.normalize_text(row.product_name), row.price))
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

    tracker.log(f"Ozet: eslesen={len(rows)}")
    tracker.log(header)
    tracker.log(separator)
    for index, row in enumerate(rows, start=1):
        difference = row.price - row.target_price
        tracker.log(
            f"{index:>{no_width}} | "
            f"{log_cell(row.product_name, product_width)} | "
            f"{tracker.format_tl(row.price):>{price_width}} | "
            f"{tracker.format_tl(row.target_price):>{price_width}} | "
            f"{tracker.format_signed_tl(difference):>{price_width}}"
        )


tracker.log_search_price_summary = log_search_price_summary
sys.exit(tracker.main())
