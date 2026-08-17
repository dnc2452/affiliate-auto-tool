"""Safe local router for the Affiliate AI Assistant."""

from __future__ import annotations

from typing import Any, Dict

from core.database import Database
from modules.analytics_service import build_summary, generate_insights


class AffiliateAssistant:
    def __init__(self, database: Database | None = None):
        self.db = database or Database()

    def respond(self, message: str) -> Dict[str, Any]:
        text = message.casefold()
        self.db.save_assistant_message("user", message)
        if any(word in text for word in ("doanh thu", "analytics", "đơn", "hiệu quả", "giảm")):
            summary = build_summary(self.db.get_analytics_records())
            answer = "\n".join(f"- {item}" for item in generate_insights(summary))
            route = "analytics"
        elif any(word in text for word in ("tìm", "sản phẩm", "winner", "ngách")):
            products = self.db.get_products(limit=10)
            if products:
                answer = "Các sản phẩm đang được xếp hạng cao:\n" + "\n".join(
                    f"- {item['title']} — {item['winner_score']:.1f}/100 (độ tin cậy {item.get('score_confidence', 0):.0f}%)"
                    for item in products
                )
            else:
                answer = "Chưa có sản phẩm đã research. Hãy dùng Product research hoặc import CSV affiliate trước."
            route = "research"
        elif any(word in text for word in ("content", "hook", "video", "kịch bản")):
            answer = "Tôi sẽ dùng Content studio để tạo các biến thể hook, caption và voiceover sau khi bạn chọn một sản phẩm winner."
            route = "content"
        else:
            answer = "Tôi có thể hỗ trợ tìm winner, đọc analytics hoặc lên concept content. Hãy nêu sản phẩm/niche hoặc dữ liệu bạn muốn phân tích."
            route = "general"
        self.db.save_assistant_message("assistant", answer)
        return {"answer": answer, "route": route}
