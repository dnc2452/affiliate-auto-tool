import os
import re
import logging
from gtts import gTTS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class VoiceGenerator:
    """Module tự động lọc kịch bản và tạo file âm thanh tiếng Việt MP3 bằng gTTS"""

    def __init__(self, output_dir: str = "output/audio"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def clean_script_text(self, text: str) -> str:
        """Lọc bỏ các ghi chú cảnh quay trong ngoặc và tiêu đề markdown"""
        # Xóa các ghi chú trong ngoặc (...), [...], {...}
        cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', text)
        # Xóa các định dạng Markdown như **HOOK**, Narrator:, v.v.
        cleaned = re.sub(r'\*\*.*?\*\*', '', cleaned)
        cleaned = re.sub(r'(Narrator|Dẫn chương trình|MC):', '', cleaned, flags=re.IGNORECASE)
        # Gom dòng và dọn khoảng trắng thừa
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        return ' '.join(lines)

    def text_to_speech(self, text: str, filename: str = "voiceover.mp3", lang: str = "vi") -> str:
        clean_text = self.clean_script_text(text)
        if not clean_text:
            logging.error("Lỗi: Văn bản sau khi lọc ghi chú bị rỗng.")
            return None

        filepath = os.path.join(self.output_dir, filename)
        logging.info(f"Đang tạo giọng đọc tiếng Việt cho file: {filename}...")
        
        try:
            tts = gTTS(text=clean_text, lang=lang, slow=False)
            tts.save(filepath)
            logging.info(f"Đã xuất file âm thanh thành công: {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Lỗi khi tạo giọng đọc gTTS: {e}")
            return None