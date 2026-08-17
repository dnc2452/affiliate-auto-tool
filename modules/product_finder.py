"""Explainable, data-quality-aware winner scoring for affiliate products."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field


class ProductMetrics(BaseModel):
    """Canonical product record shared by research, content and analytics."""

    product_id: str
    title: str
    price: float = Field(ge=0)
    sales_count_30d: int = Field(default=0, ge=0)
    rating: float = Field(default=0, ge=0, le=5)
    review_count: int = Field(default=0, ge=0)
    commission_rate: float = Field(default=0, ge=0, le=100)
    is_official_shop: bool = False
    product_url: str = ""
    affiliate_url: str = ""
    shop_name: str = ""
    image_url: str = ""
    description: str = ""


class ProductAnalyzer:
    """Ranks products without pretending unavailable marketplace data is known."""

    def __init__(self, min_rating: float = 4.3, min_sales: int = 20):
        self.min_rating = min_rating
        self.min_sales = min_sales

    @staticmethod
    def _clamp(value: float, lower: float = 0, upper: float = 1) -> float:
        return max(lower, min(upper, value))

    def score_with_breakdown(self, product: ProductMetrics) -> Tuple[float, Dict[str, float], float, List[str]]:
        """Return score /100, weighted components, confidence and caveats."""
        demand = self._clamp(math.log1p(product.sales_count_30d) / math.log1p(3000)) * 25
        rating = (product.rating / 5) * 15 if product.rating else 0
        review_trust = self._clamp(math.log1p(product.review_count) / math.log1p(1000)) * 10
        commission = self._clamp(product.commission_rate / 20) * 18 if product.commission_rate else 0
        price_fit = 12 * math.exp(-((math.log10(max(product.price, 1)) - 5.25) ** 2) / 1.8)
        trust = 8 if product.is_official_shop else 4
        content_potential = 12 if product.image_url or product.description else 5
        breakdown = {
            "demand": round(demand, 2), "rating": round(rating, 2),
            "review_trust": round(review_trust, 2), "commission": round(commission, 2),
            "price_fit": round(price_fit, 2), "shop_trust": round(trust, 2),
            "content_potential": round(content_potential, 2),
        }
        score = round(sum(breakdown.values()), 2)
        known = sum((product.sales_count_30d > 0, product.rating > 0, product.review_count > 0,
                     product.commission_rate > 0, bool(product.product_url),
                     bool(product.image_url or product.description)))
        confidence = round(known / 6 * 100, 1)
        caveats: List[str] = []
        if not product.commission_rate:
            caveats.append("Chưa có hoa hồng: xác minh trong affiliate portal trước khi sản xuất content.")
        if not product.sales_count_30d:
            caveats.append("Chưa lấy được số bán 30 ngày: điểm demand có độ tin cậy thấp.")
        if not product.review_count:
            caveats.append("Chưa lấy được số review: cần kiểm tra chất lượng phản hồi thủ công.")
        if product.rating and product.rating < self.min_rating:
            caveats.append(f"Rating dưới ngưỡng khuyến nghị {self.min_rating:.1f}/5.")
        if product.sales_count_30d and product.sales_count_30d < self.min_sales:
            caveats.append(f"Số bán dưới ngưỡng tham chiếu {self.min_sales} đơn/30 ngày.")
        return score, breakdown, confidence, caveats

    def calculate_winner_score(self, product: ProductMetrics) -> float:
        return self.score_with_breakdown(product)[0]

    def analyze(self, product: ProductMetrics) -> Dict[str, Any]:
        score, breakdown, confidence, caveats = self.score_with_breakdown(product)
        result = product.model_dump()
        result.update(winner_score=score, score_breakdown=breakdown, score_confidence=confidence,
                      score_caveats=caveats,
                      qualification="winner" if score >= 60 and confidence >= 50 else "needs_review")
        return result

    def filter_winner_products(self, raw_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for item in raw_products:
            try:
                analyzed = self.analyze(ProductMetrics(**item))
            except Exception:
                continue
            if analyzed["winner_score"] >= 60:
                results.append(analyzed)
        return sorted(results, key=lambda item: item["winner_score"], reverse=True)
