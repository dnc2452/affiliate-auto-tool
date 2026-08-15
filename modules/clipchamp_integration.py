import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ClipchampLauncher:
    """Module tự động mở Microsoft Clipchamp và điều hướng tới thư mục chứa tài nguyên video/audio."""
    def __init__(self):
        pass

    def launch_and_open_assets(self, video_path: str = None, audio_path: str = None):
        """
        Khởi chạy Microsoft Clipchamp và mở thư mục chứa tài nguyên trong File Explorer.
        """
        logging.info("🚀 Đang khởi chạy Microsoft Clipchamp...")

        # 1. Khởi chạy ứng dụng Clipchamp qua URI Scheme của Windows
        try:
            subprocess.run(["cmd", "/c", "start", "ms-clipchamp:"], shell=True, check=True)
            logging.info("✅ Đã mở thành công Microsoft Clipchamp!")
        except Exception as e:
            logging.warning(f"⚠️ Không thể mở Clipchamp tự động: {e}. Bạn có thể mở Clipchamp thủ công từ Start Menu.")

        # 2. Định vị và mở thư mục chứa tài nguyên đã tạo
        target_dir = None
        if video_path and os.path.exists(video_path):
            target_dir = os.path.abspath(os.path.dirname(video_path))
        elif audio_path and os.path.exists(audio_path):
            target_dir = os.path.abspath(os.path.dirname(audio_path))
        else:
            target_dir = os.path.abspath("output")

        if os.path.exists(target_dir):
            logging.info(f"📂 Đang mở thư mục chứa file thành phẩm: {target_dir}")
            try:
                # Mở File Explorer và highlight trực tiếp file video
                if video_path and os.path.exists(video_path):
                    subprocess.run(f'explorer /select,"{os.path.abspath(video_path)}"', shell=True)
                else:
                    subprocess.run(f'explorer "{target_dir}"', shell=True)
            except Exception as e:
                logging.warning(f"Không thể mở thư mục File Explorer: {e}")

if __name__ == "__main__":
    launcher = ClipchampLauncher()
    launcher.launch_and_open_assets()