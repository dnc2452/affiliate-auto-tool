"""Research agent: collect real public product data, then score transparently."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.base_agent import BaseAgent
from core.config import DEFAULT_SEARCH_LIMIT, MIN_WINNER_SCORE
from modules.marketplace_scraper import MarketplaceScraper, ResearchUnavailable
from modules.product_finder import ProductAnalyzer, ProductMetrics


class ResearchAgent(BaseAgent):
    def __init__(self, scraper: Optional[MarketplaceScraper] = None, analyzer: Optional[ProductAnalyzer] = None):
        super().__init__(name="ResearchAgent")
        self.scraper = scraper or MarketplaceScraper()
        self.analyzer = analyzer or ProductAnalyzer()

    def run(self, keyword: str = "", products: Optional[List[Dict[str, Any]]] = None,
            platform: str = "shopee", limit: int = DEFAULT_SEARCH_LIMIT,
            min_score: float = MIN_WINNER_SCORE, save_to_db: bool = True,
            use_demo: bool = False) -> List[Dict[str, Any]]:
        """Research products. Demo data is available only when explicitly requested."""
        if platform not in {"shopee", "tiktok", "lazada"}:
            raise ValueError("Platform phải là shopee, tiktok hoặc lazada.")
        source = "provided"
        if products:
            raw_products = products
        elif use_demo:
            source = "demo"
            raw_products = self._get_demo_products(keyword or "sản phẩm affiliate")
        else:
            source = "playwright_public"
            try:
                raw_products = self.scraper.search(keyword, platform, limit)
            except ResearchUnavailable as error:
                self.db.record_research_run(keyword, platform, source, limit, error_message=str(error))
                self.log_warning(str(error))
                return []

        scored = self._score_products(raw_products, platform, source)
        winners = sorted((item for item in scored if item["winner_score"] >= min_score),
                         key=lambda item: item["winner_score"], reverse=True)[:limit]
        if save_to_db:
            for product in winners:
                product["db_id"] = self.db.save_product(product)
        self.db.record_research_run(keyword, platform, source, limit, result_count=len(winners))
        self.log_info(f"Research hoàn tất: {len(winners)} sản phẩm đạt score ≥ {min_score}.")
        return winners

    def _score_products(self, raw_products: List[Dict[str, Any]], platform: str, source: str) -> List[Dict[str, Any]]:
        scored: List[Dict[str, Any]] = []
        for item in raw_products:
            try:
                metrics = ProductMetrics(
                    product_id=str(item.get("product_id") or item.get("id") or item.get("product_url") or item.get("title", "")),
                    title=item.get("title") or item.get("name") or "Không có tên",
                    price=float(item.get("price") or 0),
                    sales_count_30d=int(item.get("sales_count") or item.get("sales_count_30d") or item.get("sold") or 0),
                    rating=float(item.get("rating") or 0), review_count=int(item.get("review_count") or item.get("reviews") or 0),
                    commission_rate=float(item.get("commission_rate") or item.get("commission") or 0),
                    is_official_shop=bool(item.get("is_official_shop") or item.get("official") or False),
                    product_url=item.get("product_url") or item.get("url") or "",
                    affiliate_url=item.get("affiliate_url") or "", shop_name=item.get("shop_name") or "",
                    image_url=item.get("image_url") or "", description=item.get("description") or item.get("desc") or "",
                )
                result = self.analyzer.analyze(metrics)
                result.update(platform=platform, source=item.get("source") or source)
                scored.append(result)
            except Exception as error:
                self.log_warning(f"Bỏ qua sản phẩm có dữ liệu không hợp lệ: {error}")
        return scored

    @staticmethod
    def _get_demo_products(keyword: str) -> List[Dict[str, Any]]:
        return [{"product_id": "demo_001", "title": f"Sản phẩm demo {keyword}", "price": 199000,
                 "sales_count": 850, "rating": 4.8, "review_count": 340, "commission_rate": 15,
                 "is_official_shop": True, "product_url": "https://example.invalid/demo", "source": "demo"}]
