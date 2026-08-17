import sys
from pathlib import Path
from typing import List, Dict, Optional, Any

# Thêm thư mục gốc project vào sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.research_agent import ResearchAgent
from agents.content_agent import ContentAgent
from agents.video_agent import VideoAgent


class AffiliatePipeline:
    """
    Pipeline chính: Research → Content → Video
    """

    def __init__(self):
        self.research = ResearchAgent()
        self.content = ContentAgent()
        self.video = VideoAgent()

    def run(
        self,
        keyword: str = "",
        products: Optional[List[Dict]] = None,
        platform: str = "shopee",
        image_paths: Optional[List[str]] = None,
        limit: int = 3,
        min_score: float = 60,
        use_demo: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Chạy toàn bộ quy trình.

        Returns:
            Danh sách kết quả cuối cùng (mỗi item chứa product + content + audio/video)
        """
        print("=" * 60)
        print("BẮT ĐẦU PIPELINE AFFILIATE AUTO")
        print("=" * 60)

        # 1. Research
        print("\n[1/3] RESEARCH AGENT")
        winners = self.research.run(
            keyword=keyword,
            products=products,
            platform=platform,
            limit=limit,
            min_score=min_score,
            use_demo=use_demo,
        )

        if not winners:
            print("Không tìm thấy sản phẩm đạt chuẩn.")
            return []

        print(f"→ Tìm thấy {len(winners)} sản phẩm winner")

        final_results = []

        for idx, product in enumerate(winners, 1):
            print(f"\n{'='*40}")
            print(f"Xử lý sản phẩm {idx}/{len(winners)}: {product.get('title')}")
            print(f"{'='*40}")

            # 2. Content
            print("\n[2/3] CONTENT AGENT")
            content_result = self.content.run(product=product)

            if not content_result:
                print("→ Bỏ qua vì không tạo được nội dung")
                continue

            # 3. Video
            print("\n[3/3] VIDEO AGENT")
            video_result = self.video.run(
                content=content_result,
                image_paths=image_paths
            )

            final_results.append({
                "product": product,
                "content": content_result,
                "media": video_result
            })

        print("\n" + "=" * 60)
        print(f"HOÀN THÀNH PIPELINE | Thành công: {len(final_results)}/{len(winners)}")
        print("=" * 60)

        return final_results


# Test nhanh
if __name__ == "__main__":
    pipeline = AffiliatePipeline()

    # Cách 1: Dùng dữ liệu demo (không cần ảnh)
    results = pipeline.run(
        keyword="dầu gội phủ bạc",
        limit=2,
        use_demo=True,
    )

    # Cách 2: Nếu muốn test với ảnh thật, bỏ comment đoạn dưới
    # results = pipeline.run(
    #     keyword="dầu gội phủ bạc",
    #     image_paths=["path/to/anh1.jpg", "path/to/anh2.jpg"],
    #     limit=1
    # )

    print("\n=== TÓM TẮT KẾT QUẢ ===")
    for i, item in enumerate(results, 1):
        p = item["product"]
        c = item["content"]
        m = item["media"]
        print(f"\n{i}. {p.get('title')}")
        print(f"   Score : {p.get('winner_score')}")
        print(f"   Model : {c.get('used_model')}")
        print(f"   Audio : {m.get('audio_path') if m else None}")
        print(f"   Video : {m.get('video_path') if m else None}")
