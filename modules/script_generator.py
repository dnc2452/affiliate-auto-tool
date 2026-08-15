import os
import json
import base64
import logging
import random
import requests
from typing import Dict, Optional, List
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class VideoScript(BaseModel):
    product_title: str
    voiceover: str
    caption: str
    seeding_comments: List[str]
    used_model: str

class MultiModelScriptGenerator:
    """Module tạo nội dung Affiliate linh hoạt hỗ trợ tất cả Key trong .env:
    Gemini, Groq, OpenRouter, OpenAI, AIMLAPI, Cerebras, NVIDIA
    """

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.aiml_key = os.getenv("AIMLAPI_KEY")
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY")
        self.nvidia_key = os.getenv("NVIDIA_API_KEY")

    def _encode_image(self, image_path: str) -> Optional[str]:
        try:
            if os.path.exists(image_path):
                with open(image_path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            logging.warning(f"Không thể đọc file ảnh {image_path}: {e}")
        return None

    def analyze_product_image(self, image_path: str) -> Optional[str]:
        api_key = self.gemini_key or os.getenv("GEMINI_API_KEY")
        if not api_key or not os.path.exists(image_path):
            return None

        b64_img = self._encode_image(image_path)
        if not b64_img:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": "Hãy nhìn kĩ hình ảnh này và cho biết đây là sản phẩm gì (tên sản phẩm, kiểu dáng, chất liệu, màu sắc, công dụng). Trả lời ngắn gọn dưới 40 từ tiếng Việt."},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}}
                ]
            }]
        }
        try:
            res = requests.post(url, json=payload, timeout=20)
            if res.status_code == 200:
                desc = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                logging.info(f"👁️ Vision AI đã quét ảnh: {desc}")
                return desc
        except Exception as e:
            logging.warning(f"Phân tích Vision AI lỗi: {e}")
        return None

    # --- CÁC HÀM GỌI PROVIDER ---

    def _call_cerebras(self, prompt: str) -> Optional[str]:
        """Cerebras API - Tốc độ cực nhanh"""
        api_key = self.cerebras_key or os.getenv("CEREBRAS_API_KEY")
        if not api_key: return None
        url = "https://api.cerebras.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama3.1-70b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            logging.warning(f"Cerebras lỗi {res.status_code}: {res.text}")
        except Exception as e:
            logging.warning(f"Cerebras Exception: {e}")
        return None

    def _call_aimlapi(self, prompt: str) -> Optional[str]:
        """AIML API (Hỗ trợ rất nhiều model)"""
        api_key = self.aiml_key or os.getenv("AIMLAPI_KEY")
        if not api_key: return None
        url = "https://api.aimlapi.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            logging.warning(f"AIMLAPI lỗi {res.status_code}: {res.text}")
        except Exception as e:
            logging.warning(f"AIMLAPI Exception: {e}")
        return None

    def _call_groq(self, prompt: str) -> Optional[str]:
        api_key = self.groq_key or os.getenv("GROQ_API_KEY")
        if not api_key: return None
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            logging.warning(f"Groq lỗi {res.status_code}: {res.text}")
        except Exception as e:
            logging.warning(f"Groq Exception: {e}")
        return None

    def _call_openrouter(self, prompt: str) -> Optional[str]:
        api_key = self.openrouter_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key: return None
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000"
        }
        payload = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            logging.warning(f"OpenRouter lỗi {res.status_code}: {res.text}")
        except Exception as e:
            logging.warning(f"OpenRouter Exception: {e}")
        return None

    def _call_gemini(self, prompt: str) -> Optional[str]:
        api_key = self.gemini_key or os.getenv("GEMINI_API_KEY")
        if not api_key: return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                return res.json()["candidates"][0]["content"]["parts"][0]["text"]
            logging.warning(f"Gemini lỗi {res.status_code}: {res.text}")
        except Exception as e:
            logging.warning(f"Gemini Exception: {e}")
        return None

    def _call_chatgpt(self, prompt: str) -> Optional[str]:
        api_key = self.openai_key or os.getenv("OPENAI_API_KEY")
        if not api_key: return None
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Bạn là chuyên gia Marketing Affiliate Short Video."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            logging.warning(f"ChatGPT lỗi {res.status_code}: {res.text}")
        except Exception as e:
            logging.warning(f"ChatGPT Exception: {e}")
        return None

    def _call_nvidia_nim(self, prompt: str) -> Optional[str]:
        api_key = self.nvidia_key or os.getenv("NVIDIA_API_KEY")
        if not api_key: return None
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "meta/llama-3.3-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            logging.warning(f"NVIDIA lỗi {res.status_code}: {res.text}")
        except Exception as e:
            logging.warning(f"NVIDIA Exception: {e}")
        return None

    def generate_script(self, product_info: Dict, sample_image_path: Optional[str] = None) -> Optional[VideoScript]:
        raw_price = product_info.get('price', 0)
        try:
            formatted_price = f"{int(raw_price):,} VNĐ"
        except (ValueError, TypeError):
            formatted_price = f"{raw_price} VNĐ" if raw_price else "Liên hệ"

        title = product_info.get('title', 'Sản phẩm')
        desc = product_info.get('description', '')

        image_analysis_prompt = ""
        if sample_image_path and os.path.exists(sample_image_path):
            vision_desc = self.analyze_product_image(sample_image_path)
            if vision_desc:
                image_analysis_prompt = f"- Phân tích thực tế từ ảnh upload: {vision_desc}"

        prompt = f"""
Bạn là một chuyên gia Marketing Affiliate TikTok/Reels đỉnh cao.
Hãy tạo bộ nội dung bán hàng khớp 100% với thông tin sản phẩm sau:
- Tên sản phẩm: {title}
- Mô tả & Đặc tính sản phẩm: {desc}
{image_analysis_prompt}
- Giá bán: {formatted_price}

YÊU CẦU ĐẦU RA BẮT BUỘC CHỈ LÀ MỘT CHUỖI JSON HỢP LỆ (KHÔNG VIẾT BẤT KỲ CÂU DẪN NÀO BÊN NGOÀI):
{{
  "voiceover": "Lời đọc lồng tiếng ngắn gọn 15-20 giây. Viết bằng văn bản thuần túy 100%, KHÔNG chứa ký tự đặc biệt, KHÔNG ghi chú [HOOK], KHÔNG ghi chú chuyển cảnh. Tập trung mô tả đúng điểm ăn tiền của sản phẩm {title} và kêu gọi bấm vào giỏ hàng ngay.",
  "caption": "Đoạn caption TikTok gây chú ý mạnh bằng tâm lý FOMO/Hook thu hút, đính kèm 4-5 hashtag hot phù hợp.",
  "seeding_comments": [
    "Bình luận mồi 1 (hỏi giá/ưu đãi)",
    "Bình luận mồi 2 (hỏi tính năng/chất liệu/bảo hành)",
    "Bình luận mồi 3 (khen đã dùng rất ok/giao nhanh)",
    "Bình luận mồi 4 (hỏi link mua ở đâu)",
    "Bình luận mồi 5 (thắc mắc chính sách đổi trả)"
  ]
}}
"""

        # Danh sách TẤT CẢ các Provider có hỗ trợ
        all_providers = [
            ("Cerebras (Llama-3.1 70B)", self._call_cerebras, self.cerebras_key or os.getenv("CEREBRAS_API_KEY")),
            ("AIML API (Llama-3.3)", self._call_aimlapi, self.aiml_key or os.getenv("AIMLAPI_KEY")),
            ("Groq (Llama-3.3)", self._call_groq, self.groq_key or os.getenv("GROQ_API_KEY")),
            ("OpenRouter (Free Llama)", self._call_openrouter, self.openrouter_key or os.getenv("OPENROUTER_API_KEY")),
            ("Google Gemini", self._call_gemini, self.gemini_key or os.getenv("GEMINI_API_KEY")),
            ("ChatGPT (GPT-4o-mini)", self._call_chatgpt, self.openai_key or os.getenv("OPENAI_API_KEY")),
            ("NVIDIA NIM (Llama-3.3)", self._call_nvidia_nim, self.nvidia_key or os.getenv("NVIDIA_API_KEY")),
        ]

        # Lọc các con ĐÃ CÓ KEY trong .env
        available = [(name, func) for name, func, key in all_providers if key]

        if not available:
            logging.error("❌ Không tìm thấy bất kỳ API Key hợp lệ nào trong file .env!")
            return None

        # Ngẫu nhiên xáo trộn thứ tự gọi để tool tự động linh hoạt, không bị cứng nhắc
        random.shuffle(available)

        for name, func in available:
            logging.info(f"🔄 [Auto-Pick] Đang thử kết nối AI Model: {name}...")
            raw_response = func(prompt)
            if raw_response:
                try:
                    cleaned = raw_response.strip()
                    if "```json" in cleaned:
                        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
                    elif "```" in cleaned:
                        cleaned = cleaned.split("```")[1].split("```")[0].strip()

                    data = json.loads(cleaned)
                    logging.info(f"🎉 TẠO KỊCH BẢN THÀNH CÔNG BẰNG MODEL: {name}")
                    return VideoScript(
                        product_title=title,
                        voiceover=data.get("voiceover", ""),
                        caption=data.get("caption", ""),
                        seeding_comments=data.get("seeding_comments", []),
                        used_model=name
                    )
                except Exception as parse_err:
                    logging.warning(f"⚠️ {name} phản hồi không đúng JSON format. Tự chuyển model tiếp theo...")

        logging.error("❌ Tất cả các Provider trong .env đều không phản hồi thành công!")
        return None