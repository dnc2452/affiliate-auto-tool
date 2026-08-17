import sys
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime

# Thêm thư mục gốc project vào sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.base_agent import BaseAgent
from core.config import OUTPUT_DIR
from modules.voice_generator import VoiceGenerator
from modules.video_creator import VideoCreator


class VideoAgent(BaseAgent):
    """
    Agent tạo audio + video từ nội dung của ContentAgent.
    """

    def __init__(self):
        super().__init__(name="VideoAgent")
        self.voice_gen = VoiceGenerator(output_dir=str(OUTPUT_DIR / "audio"))
        self.video_creator = VideoCreator(output_dir=str(OUTPUT_DIR / "videos"))

    def run(
        self,
        content: Dict[str, Any],
        image_paths: Optional[List[str]] = None,
        output_name: Optional[str] = None,
        save_to_db: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Tạo audio + video từ content.

        Args:
            content: kết quả từ ContentAgent (phải có 'voiceover')
            image_paths: danh sách đường dẫn ảnh (bắt buộc để render video)
            output_name: tên file video (không cần đuôi .mp4)
            save_to_db: có lưu thông tin video không

        Returns:
            dict chứa audio_path, video_path...
        """
        voiceover = content.get("voiceover")
        if not voiceover:
            self.log_error("Không có voiceover trong content")
            return None

        title = content.get("product_title") or content.get("product", {}).get("title") or "video"
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()[:40]
        safe_title = safe_title.replace(" ", "_")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = output_name or f"{safe_title}_{timestamp}"

        # -------------------------------------------------
        # 1. Tạo audio
        # -------------------------------------------------
        self.log_info("Đang tạo file audio...")
        audio_filename = f"{base_name}.mp3"
        audio_path = self.voice_gen.text_to_speech(
            text=voiceover,
            filename=audio_filename
        )

        if not audio_path:
            self.log_error("Tạo audio thất bại")
            return None

        self.log_info(f"Audio đã tạo: {audio_path}")

        # -------------------------------------------------
        # 2. Tạo video (nếu có ảnh)
        # -------------------------------------------------
        video_path = None

        if image_paths and len(image_paths) > 0:
            # Lọc ảnh tồn tại
            valid_images = [p for p in image_paths if Path(p).exists()]

            if not valid_images:
                self.log_warning("Không có ảnh hợp lệ → chỉ tạo audio")
            else:
                self.log_info(f"Đang render video từ {len(valid_images)} ảnh...")
                video_filename = f"{base_name}.mp4"

                video_path = self.video_creator.create_video_from_images(
                    image_paths=valid_images,
                    audio_path=audio_path,
                    output_filename=video_filename
                )

                if video_path:
                    self.log_info(f"Video đã tạo: {video_path}")
                else:
                    self.log_error("Render video thất bại")
        else:
            self.log_warning("Không cung cấp image_paths → chỉ tạo audio")

        result = {
            "audio_path": audio_path,
            "video_path": video_path,
            "content": content,
            "base_name": base_name,
        }

        # -------------------------------------------------
        # 3. Lưu thông tin (nếu cần)
        # -------------------------------------------------
        if save_to_db and content.get("content_id"):
            try:
                # Tạm thời chỉ log, sau này mở rộng bảng videos
                self.log_info(f"Video liên kết với content_id={content.get('content_id')}")
            except Exception as e:
                self.log_error(f"Lỗi lưu video info: {e}")

        return result


# Test nhanh
if __name__ == "__main__":
    # Giả lập content từ ContentAgent
    demo_content = {
        "product_title": "Combo dầu gội phủ bạc tiết kiệm",
        "voiceover": "Đừng tốn tiền đi tiệm nhuộm tóc hóa chất độc hại nữa. Đây là combo dầu gội phủ bạc giúp tóc đen tự nhiên chỉ sau mười lăm phút ngay tại nhà. Thành phần thảo dược an toàn thơm mát không gây kích ứng da đầu. Dùng cực kỳ tiết kiệm cho cả gia đình. Bấm ngay vào giỏ hàng bên dưới để sở hữu mái tóc thanh xuân với giá ưu đãi nhé.",
        "caption": "Tạm biệt tóc bạc chỉ sau 15 phút tại nhà!",
        "seeding_comments": [],
        "used_model": "Google Gemini",
        "content_id": 1
    }

    agent = VideoAgent()

    # Test chỉ tạo audio (không có ảnh)
    result = agent.run(content=demo_content)

    if result:
        print("\n=== KẾT QUẢ VIDEO AGENT ===")
        print(f"Audio: {result['audio_path']}")
        print(f"Video: {result['video_path']}")
    else:
        print("Tạo video/audio thất bại")