import sys
from pathlib import Path

# Thêm thư mục gốc project vào sys.path để import được core và modules
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import re
import time
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus

from core.base_agent import BaseAgent
from core.config import DEFAULT_SEARCH_LIMIT, MIN_WINNER_SCORE, USER_AGENT

# Import module chấm điểm sẵn có của bạn
try:
    from modules.product_finder import ProductAnalyzer, ProductMetrics
except ImportError:
    ProductAnalyzer = None
    ProductMetrics = None


class ResearchAgent(BaseAgent):
    """
    Agent tìm và đánh giá sản phẩm affiliate.
    Hiện tại hỗ trợ:
    - Nhập thủ công danh sách sản phẩm
    - Tìm kiếm công khai đơn giản (placeholder, dễ mở rộng)
    - Chấm điểm Winner bằng ProductAnalyzer có sẵn
    - Lưu vào database
    """

    def __init__(self):
        super().__init__(name="ResearchAgent")
        self.analyzer = ProductAnalyzer() if ProductAnalyzer else None

    def run(
        self,
        keyword: str = "",
        products: Optional[List[Dict]] = None,
        platform: str = "shopee",
        limit: int = DEFAULT_SEARCH_LIMIT,
        min_score: float = MIN_WINNER_SCORE,
        save_to_db: bool = True
    ) -> List[Dict]:
        """
        Hàm chính của Research Agent.

        Cách dùng:
        1. Truyền sẵn danh sách products (khuyến nghị giai đoạn đầu)
        2. Hoặc chỉ truyền keyword (sẽ dùng nguồn free / placeholder)
        """
        self.log_info(f"Bắt đầu nghiên cứu sản phẩm | keyword='{keyword}' | platform={platform}")

        raw_products = []

        # Ưu tiên dùng dữ liệu người dùng truyền vào
        if products and isinstance(products, list) and len(products) > 0:
            self.log_info(f"Sử dụng {len(products)} sản phẩm được truyền vào")
            raw_products = products
        else:
            # Placeholder: sau này thay bằng Playwright / API free
            self.log_warning("Chưa có nguồn crawl free ổn định. Đang dùng dữ liệu mẫu để test pipeline.")
            raw_products = self._get_demo_products(keyword or "sản phẩm affiliate")

        # Chuẩn hóa + chấm điểm
        scored_products = self._score_products(raw_products, platform)

        # Lọc theo điểm tối thiểu
        winners = [p for p in scored_products if p.get("winner_score", 0) >= min_score]
        winners = sorted(winners, key=lambda x: x.get("winner_score", 0), reverse=True)[:limit]

        self.log_info(f"Tìm thấy {len(winners)} sản phẩm đạt chuẩn (score >= {min_score})")

        # Lưu database
        if save_to_db and winners:
            for p in winners:
                try:
                    db_id = self.db.save_product(p)
                    p["db_id"] = db_id
                except Exception as e:
                    self.log_error(f"Lỗi lưu database: {e}")

        return winners

    def _score_products(self, raw_products: List[Dict], platform: str) -> List[Dict]:
        """Dùng ProductAnalyzer cũ để chấm điểm"""
        if not self.analyzer:
            self.log_warning("ProductAnalyzer không khả dụng, bỏ qua chấm điểm")
            for p in raw_products:
                p["platform"] = platform
                p["winner_score"] = 50.0
            return raw_products

        scored = []
        for item in raw_products:
            try:
                # Chuẩn hóa dữ liệu đầu vào cho ProductMetrics
                normalized = {
                    "product_id": str(item.get("product_id") or item.get("id") or item.get("title", "")[:20]),
                    "title": item.get("title") or item.get("name") or "Không có tên",
                    "price": float(item.get("price") or 0),
                    "sales_count_30d": int(item.get("sales_count") or item.get("sales_count_30d") or item.get("sold") or 0),
                    "rating": float(item.get("rating") or 4.5),
                    "commission_rate": float(item.get("commission_rate") or item.get("commission") or 10.0),
                    "is_official_shop": bool(item.get("is_official_shop") or item.get("official") or False),
                    "product_url": item.get("product_url") or item.get("url") or "",
                }

                metrics = ProductMetrics(**normalized)
                score = self.analyzer.calculate_winner_score(metrics)

                result = normalized.copy()
                result["winner_score"] = score
                result["platform"] = platform
                scored.append(result)

            except Exception as e:
                self.log_warning(f"Bỏ qua sản phẩm lỗi: {e}")
                continue

        return scored

    def _get_demo_products(self, keyword: str) -> List[Dict]:
        """Dữ liệu mẫu để test pipeline khi chưa có crawl thật"""
        return [
            {
                "product_id": "demo_001",
                "title": f"Sản phẩm demo liên quan {keyword} - Phiên bản cao cấp",
                "price": 199000,
                "sales_count": 850,
                "rating": 4.8,
                "commission_rate": 15.0,
                "is_official_shop": True,
                "product_url": "https://shopee.vn/demo-product-1"
            },
            {
                "product_id": "demo_002",
                "title": f"{keyword} chính hãng - Giá tốt",
                "price": 149000,
                "sales_count": 320,
                "rating": 4.6,
                "commission_rate": 12.0,
                "is_official_shop": False,
                "product_url": "https://shopee.vn/demo-product-2"
            },
            {
                "product_id": "demo_003",
                "title": f"Combo {keyword} tiết kiệm",
                "price": 299000,
                "sales_count": 1200,
                "rating": 4.9,
                "commission_rate": 18.0,
                "is_official_shop": True,
                "product_url": "https://shopee.vn/demo-product-3"
            },
        ]


# Test nhanh khi chạy trực tiếp file này
if __name__ == "__main__":
    agent = ResearchAgent()
    results = agent.run(keyword="dầu gội phủ bạc", limit=5)
    print("\n=== KẾT QUẢ RESEARCH AGENT ===")
    for p in results:
        print(f"[{p.get('winner_score')}] {p.get('title')} - {p.get('price'):,.0f}đ")