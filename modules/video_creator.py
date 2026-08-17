import os
import logging
from typing import List, Optional

from PIL import Image as PILImage

# MoviePy tương thích nhiều version
try:
    from moviepy import (
        ImageClip,
        VideoFileClip,
        AudioFileClip,
        concatenate_videoclips
    )
except ImportError:
    from moviepy.editor import (
        ImageClip,
        VideoFileClip,
        AudioFileClip,
        concatenate_videoclips
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class VideoCreator:
    """
    Render video TikTok/Reels.

    Hỗ trợ:
    - Ảnh -> Video
    - Video -> Voiceover
    - Ảnh + Video
    """

    def __init__(self, output_dir="output/videos"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    # =====================================================
    # IMAGE PROCESS
    # =====================================================

    def prepare_image(
        self,
        img_path,
        target_size=(1080, 1920)
    ):
        """
        Auto crop 9:16
        """

        img = PILImage.open(img_path).convert("RGB")

        img_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]

        if img_ratio > target_ratio:

            new_width = int(target_size[1] * img_ratio)

            img = img.resize(
                (new_width, target_size[1]),
                PILImage.Resampling.LANCZOS
            )

            left = (new_width - target_size[0]) // 2

            img = img.crop(
                (
                    left,
                    0,
                    left + target_size[0],
                    target_size[1]
                )
            )

        else:

            new_height = int(target_size[0] / img_ratio)

            img = img.resize(
                (target_size[0], new_height),
                PILImage.Resampling.LANCZOS
            )

            top = (new_height - target_size[1]) // 2

            img = img.crop(
                (
                    0,
                    top,
                    target_size[0],
                    top + target_size[1]
                )
            )

        temp_path = os.path.join(
            self.output_dir,
            f"temp_{os.path.basename(img_path)}"
        )

        img.save(temp_path)

        return temp_path

    # =====================================================
    # IMAGE -> VIDEO
    # =====================================================

    def create_video_from_images(
        self,
        image_paths: List[str],
        audio_path: str,
        output_filename="final_video.mp4"
    ) -> Optional[str]:

        if not os.path.exists(audio_path):
            logging.error("Không tìm thấy audio.")
            return None

        try:

            audio_clip = AudioFileClip(audio_path)

            total_duration = audio_clip.duration

            valid_images = [
                p for p in image_paths
                if os.path.exists(p)
            ]

            if not valid_images:
                logging.error("Không có ảnh hợp lệ.")
                return None

            duration_per_image = (
                total_duration / len(valid_images)
            )

            clips = []

            temp_files = []

            for img_path in valid_images:

                processed = self.prepare_image(img_path)

                temp_files.append(processed)

                clip = (
                    ImageClip(processed)
                    .with_duration(duration_per_image)
                )

                clips.append(clip)

            final_video = concatenate_videoclips(
                clips,
                method="compose"
            )

            final_video = final_video.with_audio(
                audio_clip
            )

            output_path = os.path.join(
                self.output_dir,
                output_filename
            )

            final_video.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None
            )

            for clip in clips:
                clip.close()

            audio_clip.close()
            final_video.close()

            for f in temp_files:
                if os.path.exists(f):
                    os.remove(f)

            return output_path

        except Exception as e:
            logging.error(f"Lỗi render ảnh: {e}")
            return None

    # =====================================================
    # VIDEO -> VOICEOVER
    # =====================================================

    def create_video_from_clips(
        self,
        video_paths: List[str],
        audio_path: str,
        output_filename="final_video.mp4"
    ) -> Optional[str]:

        if not os.path.exists(audio_path):
            logging.error("Không tìm thấy audio.")
            return None

        valid_videos = [
            p for p in video_paths
            if os.path.exists(p)
        ]

        if not valid_videos:
            logging.error("Không có video hợp lệ.")
            return None

        try:

            audio_clip = AudioFileClip(audio_path)

            clips = []

            for video_path in valid_videos:

                clip = VideoFileClip(video_path)

                clips.append(clip)

            final_video = concatenate_videoclips(
                clips,
                method="compose"
            )

            # cắt hoặc kéo dài theo voice

            if final_video.duration > audio_clip.duration:

                final_video = final_video.subclip(
                    0,
                    audio_clip.duration
                )

            final_video = final_video.with_audio(
                audio_clip
            )

            output_path = os.path.join(
                self.output_dir,
                output_filename
            )

            final_video.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None
            )

            for clip in clips:
                clip.close()

            audio_clip.close()
            final_video.close()

            return output_path

        except Exception as e:
            logging.error(f"Lỗi render video: {e}")
            return None