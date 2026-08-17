import sys
from pathlib import Path
from typing import Dict, Optional, List, Any

# Thêm thư mục gốc project vào sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.base_agent import BaseAgent
from modules.script_generator import MultiModelScriptGenerator, VideoScript


class ContentAgent(BaseAgent):
    """
    Agent tạo nội dung (kịch bản + caption + seeding)
    dựa trên sản phẩm từ ResearchAgent.
    """

    def __init__(self):
        super().__init__(name="ContentAgent")
        self.generator = MultiModelScriptGenerator()

    def run(
        self,
        product: Dict[str, Any],
        image_path: Optional[str] = None,
        save_to_db: bool = True,
        language: str = "vi",
    ) -> Optional[Dict[str, Any]]:
        """
        Tạo nội dung cho 1 sản phẩm.

        Args:
            product: dict sản phẩm (từ ResearchAgent)
            image_path: đường dẫn ảnh sản phẩm (nếu có)
            save_to_db: có lưu vào database không

        Returns:
            dict chứa voiceover, caption, seeding_comments, used_model...
        """
        title = product.get("title") or product.get("name") or "Sản phẩm"
        self.log_info(f"Bắt đầu tạo nội dung cho: {title}")

        # Chuẩn bị dữ liệu đầu vào cho script_generator
        product_info = {
            "title": title,
            "price": product.get("price", 0),
            "description": product.get("description") or product.get("desc") or "",
            "product_url": product.get("product_url") or product.get("url") or "",
            "commission_rate": product.get("commission_rate"),
            "rating": product.get("rating"),
            "sales_count": product.get("sales_count") or product.get("sales_count_30d"),
        }

        try:
            script: Optional[VideoScript] = self.generator.generate_script(
                product_info=product_info,
                sample_image_path=image_path,
                language=language,
            )
        except Exception as e:
            self.log_error(f"Lỗi khi gọi MultiModelScriptGenerator: {e}")
            return None

        if not script:
            self.log_error("Không tạo được kịch bản (tất cả model đều thất bại hoặc thiếu API key)")
            return None

        result = {
            "product_title": script.product_title,
            "voiceover": script.voiceover,
            "caption": script.caption,
            "seeding_comments": script.seeding_comments,
            "used_model": script.used_model,
            "language": language,
            "hook": self._hook_from_voiceover(script.voiceover, language),
            "hashtags": self._hashtags_for(product),
            "product": product,          # giữ lại thông tin sản phẩm gốc
        }

        self.log_info(f"Tạo nội dung thành công bằng model: {script.used_model}")

        # Lưu vào database nếu có db_id
        product_db_id = product.get("db_id") or product.get("id")
        if save_to_db and product_db_id:
            try:
                content_id = self.db.save_content(
                    product_db_id=int(product_db_id),
                    content={
                        "voiceover": script.voiceover,
                        "caption": script.caption,
                        "seeding_comments": script.seeding_comments,
                        "used_model": script.used_model,
                    }
                )
                result["content_id"] = content_id
                self.log_info(f"Đã lưu content vào database (id={content_id})")
            except Exception as e:
                self.log_error(f"Lỗi lưu content vào database: {e}")

        return result

    @staticmethod
    def _hook_from_voiceover(voiceover: str, language: str = "vi") -> str:
        """Use the first sentence as a portable, editable hook."""
        first = (voiceover or "").strip().split(".", 1)[0].strip()
        return first or ("Discover this product before you buy." if language == "en" else "Khám phá sản phẩm này trước khi quyết định mua.")

    @staticmethod
    def _hashtags_for(product: Dict[str, Any]) -> str:
        title = str(product.get("title", "affiliate"))
        words = ["".join(char for char in word if char.isalnum()) for word in title.split()]
        terms = [f"#{word}" for word in words[:3] if len(word) > 2]
        return " ".join(["#affiliate", "#review", *terms])

    def run_batch(
        self,
        products: List[Dict[str, Any]],
        image_path: Optional[str] = None,
        save_to_db: bool = True
    ) -> List[Dict[str, Any]]:
        """Tạo nội dung cho nhiều sản phẩm"""
        results = []
        for idx, product in enumerate(products, 1):
            self.log_info(f"--- Xử lý sản phẩm {idx}/{len(products)} ---")
            content = self.run(product=product, image_path=image_path, save_to_db=save_to_db)
            if content:
                results.append(content)
        return results


# Test nhanh
if __name__ == "__main__":
    # Dữ liệu mẫu (giống ResearchAgent)
    demo_product = {
        "db_id": 1,
        "product_id": "demo_001",
        "title": "Combo dầu gội phủ bạc tiết kiệm",
        "price": 299000,
        "sales_count": 1200,
        "rating": 4.9,
        "commission_rate": 18.0,
        "product_url": "https://shopee.vn/demo-product-3",
        "winner_score": 96.4,
        "platform": "shopee"
    }

    agent = ContentAgent()
    result = agent.run(product=demo_product)

    if result:
        print("\n=== KẾT QUẢ CONTENT AGENT ===")
        print(f"Model dùng: {result['used_model']}")
        print(f"\nVoiceover:\n{result['voiceover']}")
        print(f"\nCaption:\n{result['caption']}")
        print(f"\nSeeding comments:")
        for c in result["seeding_comments"]:
            print(f"- {c}")
    else:
        print("Không tạo được nội dung. Kiểm tra API key trong file .env")
