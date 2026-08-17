"""Create a portable Ready-to-Post package for a verified product."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from PIL import Image

from core.config import OUTPUT_DIR


class ReadyToPostManager:
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = Path(output_dir) / "ready_to_post"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create(self, product: Dict[str, Any], content: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, str]:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", product.get("title", "product")).strip("-")[:48] or "product"
        target = self.output_dir / f"{datetime.now():%Y%m%d_%H%M%S_%f}_{slug}"
        target.mkdir(parents=True, exist_ok=False)
        files = {
            "voiceover.txt": content.get("voiceover", ""), "caption.txt": content.get("caption", ""),
            "hook.txt": content.get("hook", ""), "hashtags.txt": content.get("hashtags", ""),
            "seeding_comments.txt": "\n".join(content.get("seeding_comments", [])),
            "affiliate_link.txt": product.get("affiliate_url", "") or product.get("product_url", ""),
        }
        for name, body in files.items():
            (target / name).write_text(body, encoding="utf-8")
        thumbnail = self._copy_thumbnail(media.get("thumbnail_path"), target)
        manifest = {
            "product": product,
            "content": content,
            "media": media,
            "created_at": datetime.now().isoformat(),
            "disclosure": "Nội dung có thể chứa liên kết tiếp thị liên kết. Hãy hiển thị disclosure theo chính sách nền tảng.",
            "publication_checklist": [
                "Xác minh giá, mô tả và claim sản phẩm trước khi đăng.",
                "Xác minh affiliate link đang hoạt động và mức hoa hồng.",
                "Chỉ dùng media do bạn sở hữu hoặc có quyền sử dụng.",
                "Thêm disclosure affiliate theo yêu cầu của nền tảng.",
            ],
            "thumbnail_path": thumbnail,
        }
        manifest_path = target / "product_info.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        for source, output_name in ((media.get("video_path"), "video.mp4"), (media.get("audio_path"), "voiceover.mp3")):
            if source and Path(source).exists():
                shutil.copy2(source, target / output_name)
        return {"package_path": str(target), "manifest_path": str(manifest_path)}

    @staticmethod
    def _copy_thumbnail(source: Any, target: Path) -> str:
        if not source or not Path(source).is_file():
            return ""
        thumbnail = target / "thumbnail.jpg"
        try:
            with Image.open(source) as image:
                image.convert("RGB").save(thumbnail, "JPEG", quality=90)
            return str(thumbnail)
        except (OSError, ValueError):
            return ""
