"""Import verified product/affiliate exports without destroying historical data."""

from __future__ import annotations

import csv
import io
import re
from typing import Any, Dict, List


class ProductImportError(ValueError):
    pass


ALIASES = {
    "product_id": ("product_id", "product id", "id sản phẩm", "mã sản phẩm", "sku"),
    "title": ("title", "name", "product name", "tên sản phẩm", "sản phẩm"),
    "price": ("price", "giá", "giá bán", "sale price"),
    "sales_count": ("sales", "sold", "orders", "đã bán", "doanh số", "đơn hàng"),
    "rating": ("rating", "đánh giá", "star"),
    "review_count": ("reviews", "review count", "số review", "lượt đánh giá"),
    "commission_rate": ("commission", "commission rate", "hoa hồng", "tỷ lệ hoa hồng"),
    "product_url": ("product_url", "product url", "link sản phẩm", "url"),
    "affiliate_url": ("affiliate_url", "affiliate link", "link affiliate", "link tiếp thị"),
    "shop_name": ("shop", "shop name", "tên shop", "cửa hàng"),
}


def import_products_csv(payload: bytes, platform: str) -> List[Dict[str, Any]]:
    if not payload:
        raise ProductImportError("File CSV trống.")
    text = payload.decode("utf-8-sig", errors="replace")
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    if not rows or not rows[0]:
        raise ProductImportError("CSV phải có dòng tiêu đề và ít nhất một sản phẩm.")
    mapped = {_normalise(key): key for key in rows[0] if key}
    products: List[Dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        title = _get(row, mapped, "title")
        if not title:
            continue
        product_url = _get(row, mapped, "product_url")
        products.append({
            "product_id": _get(row, mapped, "product_id") or product_url or f"import-{index}-{title}",
            "title": title, "price": _number(_get(row, mapped, "price")),
            "sales_count": int(_number(_get(row, mapped, "sales_count"))),
            "rating": _number(_get(row, mapped, "rating")),
            "review_count": int(_number(_get(row, mapped, "review_count"))),
            "commission_rate": _number(_get(row, mapped, "commission_rate")),
            "product_url": product_url, "affiliate_url": _get(row, mapped, "affiliate_url"),
            "shop_name": _get(row, mapped, "shop_name"), "platform": platform,
            "source": "affiliate_csv_import",
        })
    if not products:
        raise ProductImportError("Không tìm thấy cột 'Tên sản phẩm' hợp lệ trong CSV.")
    return products


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold().replace("_", " "))


def _get(row: Dict[str, str], mapped: Dict[str, str], field: str) -> str:
    for alias in ALIASES[field]:
        source = mapped.get(_normalise(alias))
        if source:
            return (row.get(source) or "").strip()
    return ""


def _number(value: str) -> float:
    cleaned = re.sub(r"[^0-9,.-]", "", value or "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
