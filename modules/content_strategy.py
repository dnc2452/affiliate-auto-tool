import os
import logging
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


@dataclass
class ContentStrategyResult:
    target_audience: str
    usp: str
    pain_points: List[str]
    content_angles: List[str]
    hooks: List[str]
    video_ideas: List[str]
    captions: List[str]
    seeding_comments: List[str]
    cta_ideas: List[str]
    content_calendar: List[str]


class ContentStrategyAI:
    """
    AI Content Strategy Engine

    Sinh:
    - Khách hàng mục tiêu
    - USP
    - Pain Point
    - Hook
    - Video Ideas
    - Caption Ideas
    - CTA
    - Seeding Comments
    - Content Calendar
    """

    def __init__(self):
        pass

    def generate_strategy(self, product_info: dict) -> ContentStrategyResult:

        title = product_info.get("title", "")
        price = product_info.get("price", "")
        description = product_info.get("description", "")

        logging.info("Đang xây dựng chiến lược nội dung...")

        target_audience = (
            f"Khách hàng quan tâm tới {title}, "
            f"có nhu cầu giải quyết vấn đề thực tế liên quan đến sản phẩm."
        )

        usp = (
            f"{title} nổi bật nhờ khả năng đáp ứng nhu cầu chính của người dùng "
            f"với mức giá khoảng {price:,} VNĐ."
            if isinstance(price, (int, float))
            else f"{title} sở hữu các điểm mạnh nổi bật trên thị trường."
        )

        pain_points = [
            "Khách hàng chưa tìm được sản phẩm phù hợp.",
            "Lo ngại về chất lượng thực tế.",
            "Lo ngại bỏ tiền nhưng không hiệu quả.",
            "Khó lựa chọn giữa nhiều sản phẩm tương tự.",
            "Thiếu đánh giá thực tế từ người dùng."
        ]

        content_angles = [
            "Review thực tế sau 7 ngày sử dụng",
            "So sánh với đối thủ cùng phân khúc",
            "Test khả năng hoạt động thực tế",
            "Top lý do nên mua",
            "Những ai nên sử dụng sản phẩm này",
            "Bóc hộp và trải nghiệm đầu tiên",
            "Trước và sau khi sử dụng",
            "Giải quyết vấn đề khách hàng gặp phải",
            "Chia sẻ kinh nghiệm cá nhân",
            "Đánh giá ưu và nhược điểm"
        ]

        hooks = [
            f"Tôi đã tiếc vì không biết tới {title} sớm hơn...",
            f"Đừng mua {title} nếu bạn chưa biết điều này!",
            f"Sau 7 ngày dùng {title}, đây là kết quả...",
            f"Tôi đã thử {title} để xem có thật sự đáng tiền?",
            f"Điều khiến {title} khác biệt hoàn toàn so với đối thủ...",
            f"Sự thật ít ai nói về {title}...",
            f"{title} có thực sự tốt như quảng cáo?",
            f"Review thật 100% sau khi trải nghiệm {title}.",
            f"Đây là lý do nhiều người chọn {title}.",
            f"Nếu chỉ được chọn 1 sản phẩm, tôi sẽ chọn {title}."
        ]

        video_ideas = [
            f"Review tổng quan {title}",
            f"5 lý do nên mua {title}",
            f"Test thực tế {title}",
            f"So sánh {title} với đối thủ",
            f"Trải nghiệm sau 7 ngày",
            f"Ưu điểm nổi bật của {title}",
            f"Nhược điểm cần biết",
            f"Phù hợp với những ai?",
            f"Đánh giá chi tiết từng tính năng",
            f"Giải đáp câu hỏi thường gặp",
            f"Có nên mua {title} không?",
            f"Top mẹo sử dụng {title}",
            f"Case study khách hàng",
            f"Thử thách thực tế với {title}",
            f"Trước và sau khi sử dụng",
            f"Đập hộp sản phẩm",
            f"Đánh giá từ góc nhìn người mới",
            f"Review sau 30 ngày",
            f"Sản phẩm có đáng tiền không?",
            f"Top tính năng ít người biết"
        ]

        captions = [
            f"🔥 {title} đang được nhiều người quan tâm!",
            f"Bạn đã thử {title} chưa?",
            f"Review thật sau thời gian sử dụng {title}.",
            f"Sản phẩm đáng chú ý trong phân khúc hiện nay.",
            f"Không ngờ {title} lại hữu ích đến vậy.",
            f"Trải nghiệm thực tế khiến tôi bất ngờ.",
            f"Đây là lý do nhiều người lựa chọn sản phẩm này.",
            f"Đừng bỏ lỡ nếu bạn đang tìm giải pháp phù hợp.",
            f"Một sản phẩm đáng cân nhắc.",
            f"Link sản phẩm ở phần bình luận."
        ]

        seeding_comments = [
            "Ai dùng rồi cho xin review thật với?",
            "Mình đang phân vân sản phẩm này.",
            "Có ai mua rồi chưa?",
            "Hiệu quả thực tế thế nào vậy?",
            "So với đối thủ thì sao?",
            "Giá hiện tại có tốt không?",
            "Dùng lâu có bền không?",
            "Mình thấy khá ổn đấy.",
            "Có nên mua không mọi người?",
            "Ai đang dùng cho xin cảm nhận."
        ]

        cta_ideas = [
            "Xem thêm thông tin tại link bio.",
            "Nhấn theo dõi để xem thêm review.",
            "Để lại bình luận nếu cần tư vấn.",
            "Lưu video để tham khảo sau.",
            "Chia sẻ cho người đang cần.",
            "Xem ưu đãi mới nhất ngay hôm nay.",
            "Kiểm tra giá hiện tại tại link.",
            "Đừng bỏ lỡ chương trình giảm giá.",
            "Mua sớm để nhận ưu đãi tốt hơn.",
            "Theo dõi để cập nhật sản phẩm mới."
        ]

        content_calendar = [
            f"Ngày {i}: Video nội dung số {i}"
            for i in range(1, 31)
        ]

        return ContentStrategyResult(
            target_audience=target_audience,
            usp=usp,
            pain_points=pain_points,
            content_angles=content_angles,
            hooks=hooks,
            video_ideas=video_ideas,
            captions=captions,
            seeding_comments=seeding_comments,
            cta_ideas=cta_ideas,
            content_calendar=content_calendar
        )