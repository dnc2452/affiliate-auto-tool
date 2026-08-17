"""Historical analytics import, normalization and action-oriented insights."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from collections import defaultdict
from datetime import date
from typing import Any, Dict, List


FIELD_ALIASES = {
    "record_date": ("date", "ngày", "ngay", "created date"),
    "product_name": ("product", "product name", "tên sản phẩm", "sản phẩm"),
    "product_external_id": ("product id", "sku", "mã sản phẩm"),
    "content_name": ("content", "video", "video name", "tên video"),
    "channel": ("channel", "kênh", "platform", "nền tảng"),
    "clicks": ("clicks", "click", "lượt nhấp", "luot nhap"),
    "orders": ("orders", "order", "đơn hàng", "don hang"),
    "revenue": ("revenue", "gmv", "doanh thu", "sales amount"),
    "commission": ("commission", "hoa hồng", "hoa hong", "earnings"),
    "spend": ("spend", "ad spend", "chi phí", "chi phi", "cost"),
}


def parse_analytics_csv(payload: bytes, platform: str) -> List[Dict[str, Any]]:
    text = payload.decode("utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    if not rows or not rows[0]:
        raise ValueError("CSV analytics cần có tiêu đề cột và ít nhất một dòng dữ liệu.")
    columns = {_normalise(key): key for key in rows[0] if key}
    records: List[Dict[str, Any]] = []
    for row in rows:
        record = {field: _value(row, columns, field) for field in FIELD_ALIASES}
        for field in ("clicks", "orders"):
            record[field] = int(_number(record[field]))
        for field in ("revenue", "commission", "spend"):
            record[field] = _number(record[field])
        record["record_date"] = record["record_date"] or str(date.today())
        raw_identity = "|".join(str(record[key]) for key in sorted(record)) + f"|{platform}"
        record["record_hash"] = hashlib.sha256(raw_identity.encode()).hexdigest()
        records.append(record)
    return records


def build_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = {key: sum(float(record.get(key) or 0) for record in records) for key in ("clicks", "orders", "revenue", "commission", "spend")}
    totals["conversion_rate"] = totals["orders"] / totals["clicks"] * 100 if totals["clicks"] else 0
    totals["roi"] = ((totals["commission"] - totals["spend"]) / totals["spend"] * 100) if totals["spend"] else None
    grouped: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for record in records:
        name = record.get("product_name") or "Chưa gắn sản phẩm"
        for key in ("clicks", "orders", "revenue", "commission", "spend"):
            grouped[name][key] += float(record.get(key) or 0)
    products = []
    for name, values in grouped.items():
        values["conversion_rate"] = values["orders"] / values["clicks"] * 100 if values["clicks"] else 0
        products.append({"product_name": name, **values})
    products.sort(key=lambda item: (item["commission"], item["revenue"]), reverse=True)
    return {"totals": totals, "products": products}


def generate_insights(summary: Dict[str, Any]) -> List[str]:
    totals, products = summary["totals"], summary["products"]
    if not products:
        return ["Chưa có dữ liệu analytics. Import CSV từ nền tảng để bắt đầu vòng lặp tối ưu."]
    insights = [f"Ưu tiên tăng content cho '{products[0]['product_name']}' vì đang dẫn đầu về hoa hồng/doanh thu."]
    if totals["clicks"] and totals["conversion_rate"] < 1:
        insights.append("Tỷ lệ chuyển đổi dưới 1%: thử hook mới, proof rõ hơn và CTA ngắn hơn trước khi tăng sản lượng.")
    if totals["spend"] and totals["commission"] < totals["spend"]:
        insights.append("Chi phí đang cao hơn hoa hồng: tạm dừng scale paid traffic và ưu tiên creative thắng tự nhiên.")
    if len(products) > 1 and products[-1]["clicks"] > 0 and products[-1]["orders"] == 0:
        insights.append(f"'{products[-1]['product_name']}' có click nhưng chưa có đơn: kiểm tra giá, landing/link và độ khớp nội dung.")
    return insights


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().casefold().replace("_", " "))


def _value(row: Dict[str, str], columns: Dict[str, str], field: str) -> str:
    for alias in FIELD_ALIASES[field]:
        source = columns.get(_normalise(alias))
        if source:
            return (row.get(source) or "").strip()
    return ""


def _number(value: Any) -> float:
    clean = re.sub(r"[^0-9,.-]", "", str(value or "")).replace(",", "")
    try:
        return float(clean)
    except ValueError:
        return 0.0
