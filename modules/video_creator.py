import os
import logging
from typing import List, Optional
from PIL import Image as PILImage

# Tự động chọn cú pháp import tương thích với phiên bản MoviePy hiện tại
try:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
except ImportError:
    try:
        from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
    except ImportError:
        from moviepy.video.VideoClip import ImageClip
        from moviepy.audio.AudioClip import AudioFileClip
        from moviepy.video.compositing.concatenate import concatenate_videoclips

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class VideoCreator:
    """Module tự động căn chỉnh ảnh 9:16 và dựng video MP4 chuẩn TikTok/Reels"""

    def __init__(self, output_dir: str = "output/videos"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def prepare_image(self, img_path: str, target_size=(1080, 1920)) -> str:
        """Tự động cắt/căn giữa ảnh về đúng tỉ lệ 9:16 không bị méo"""
        img = PILImage.open(img_path).convert("RGB")
        img_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]
        
        if img_ratio > target_ratio:
            new_width = int(target_size[1] * img_ratio)
            img = img.resize((new_width, target_size[1]), PILImage.Resampling.LANCZOS)
            left = (new_width - target_size[0]) // 2
            img = img.crop((left, 0, left + target_size[0], target_size[1]))
        else:
            new_height = int(target_size[0] / img_ratio)
            img = img.resize((target_size[0], new_height), PILImage.Resampling.LANCZOS)
            top = (new_height - target_size[1]) // 2
            img = img.crop((0, top, target_size[0], top + target_size[1]))
            
        temp_path = os.path.join(self.output_dir, f"temp_{os.path.basename(img_path)}")
        img.save(temp_path)
        return temp_path

    def create_video_from_images(self, image_paths: List[str], audio_path: str, output_filename: str = "final_video.mp4") -> Optional[str]:
        if not os.path.exists(audio_path):
            logging.error(f"Lỗi: File audio không tồn tại tại {audio_path}")
            return None

        try:
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration

            valid_images = [p for p in image_paths if os.path.exists(p)]
            if not valid_images:
                logging.warning("Chưa tìm thấy ảnh thực tế. Đang tự động tạo nền 9:16 mặc định...")
                default_img_path = os.path.join(self.output_dir, "default_bg.jpg")
                bg = PILImage.new("RGB", (1080, 1920), color=(24, 24, 27))
                bg.save(default_img_path)
                valid_images = [default_img_path]

            duration_per_image = total_duration / len(valid_images)
            logging.info(f"Thời lượng video: {total_duration:.2f}s | Số ảnh: {len(valid_images)}")

            clips = []
            temp_files = []

            for img_path in valid_images:
                processed_img = self.prepare_image(img_path)
                temp_files.append(processed_img)

                try:
                    clip = ImageClip(processed_img).with_duration(duration_per_image)
                except AttributeError:
                    clip = ImageClip(processed_img).set_duration(duration_per_image)
                clips.append(clip)

            video_clip = concatenate_videoclips(clips, method="compose")
            
            try:
                video_clip = video_clip.with_audio(audio_clip)
            except AttributeError:
                video_clip = video_clip.set_audio(audio_clip)

            output_path = os.path.join(self.output_dir, output_filename)
            logging.info("Đang render file video MP4...")
            
            try:
                video_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
            except TypeError:
                video_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

            # Dọn dẹp tài nguyên
            audio_clip.close()
            video_clip.close()
            for c in clips:
                c.close()
            for tf in temp_files:
                if os.path.exists(tf):
                    os.remove(tf)

            logging.info(f"Đã tạo video thành công tại: {output_path}")
            return output_path

        except Exception as e:
            logging.error(f"Lỗi khi dựng video: {e}")
            return None