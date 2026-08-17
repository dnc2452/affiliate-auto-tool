"""Public-page marketplace research using Playwright, with no anti-bot bypasses."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List
from urllib.parse import quote_plus

from core.config import USER_AGENT


class ResearchUnavailable(RuntimeError):
    """Raised when the optional browser runtime or a public result is unavailable."""


class MarketplaceScraper:
    """Collect only publicly visible product metadata.

    Affiliate URLs and commissions are never fabricated: import them from an
    approved affiliate export or add them after verification in the portal.
    """

    TARGETS = {
        "shopee": "https://shopee.vn/search?keyword={keyword}",
        "lazada": "https://www.lazada.vn/catalog/?q={keyword}",
        "tiktok": "https://www.tiktok.com/search?q={keyword}",
    }

    def search(self, keyword: str, platform: str, limit: int = 20) -> List[Dict[str, Any]]:
        if platform not in self.TARGETS:
            raise ValueError(f"Platform chưa được hỗ trợ: {platform}")
        if not keyword.strip():
            raise ValueError("Từ khóa tìm kiếm không được để trống.")
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise ResearchUnavailable("Chưa cài Playwright. Chạy `python -m playwright install chromium` sau khi cài requirements.") from error
        url = self.TARGETS[platform].format(keyword=quote_plus(keyword.strip()))
        try:
            with sync_playwright() as playwright:
                installed_chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                launch_options = {"headless": True}
                if os.path.exists(installed_chrome):
                    launch_options["executable_path"] = installed_chrome
                browser = playwright.chromium.launch(**launch_options)
                page = browser.new_page(user_agent=USER_AGENT, viewport={"width": 1440, "height": 1200})
                page.goto(url, wait_until="domcontentloaded", timeout=45_000)
                page.wait_for_timeout(2_500)
                html = page.content()
                browser.close()
        except Exception as error:
            raise ResearchUnavailable(f"Không thể đọc trang công khai của {platform}: {error}") from error
        products = self._extract_json_ld(html, platform)
        if not products:
            raise ResearchUnavailable(f"{platform} không trả dữ liệu sản phẩm công khai có thể đọc được. Hãy dùng file export hợp lệ từ affiliate portal hoặc nhập URL sản phẩm.")
        return products[:limit]

    def _extract_json_ld(self, html: str, platform: str) -> List[Dict[str, Any]]:
        found: List[Dict[str, Any]] = []
        for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I):
            try:
                payload = json.loads(raw.strip())
            except json.JSONDecodeError:
                continue
            nodes = payload if isinstance(payload, list) else [payload]
            for node in nodes:
                if node.get("@type") != "Product":
                    continue
                offers = node.get("offers") or {}
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                aggregate = node.get("aggregateRating") or {}
                url = str(node.get("url") or offers.get("url") or "")
                title = str(node.get("name") or "").strip()
                if not title:
                    continue
                found.append({"product_id": url or title, "title": title, "price": self._number(offers.get("price")),
                              "rating": self._number(aggregate.get("ratingValue")),
                              "review_count": int(self._number(aggregate.get("reviewCount"))), "sales_count": 0,
                              "commission_rate": 0, "is_official_shop": False, "product_url": url,
                              "image_url": self._image(node.get("image")), "description": str(node.get("description") or ""),
                              "platform": platform, "source": "public_json_ld"})
        return found

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(str(value).replace(",", ""))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _image(value: Any) -> str:
        return str(value[0]) if isinstance(value, list) and value else str(value or "")
