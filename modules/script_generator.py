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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class VideoScript(BaseModel):
    product_title: str
    voiceover: str
    caption: str
    seeding_comments: List[str]
    used_model: str


class MultiModelScriptGenerator:
    """
    Module tạo nội dung Affiliate.

    Hỗ trợ:
    - Google Gemini
    - Groq
    - OpenRouter
    - OpenAI
    - AIML API
    - Cerebras
    - NVIDIA NIM
    """

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.aiml_key = os.getenv("AIMLAPI_KEY")
        self.cerebras_key = os.getenv("CEREBRAS_API_KEY")
        self.nvidia_key = os.getenv("NVIDIA_API_KEY")

    # =========================================================
    # IMAGE
    # =========================================================

    def _encode_image(self, image_path: str) -> Optional[str]:
        try:
            if os.path.exists(image_path):
                with open(image_path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception as e:
            logging.warning(
                f"Không thể đọc file ảnh {image_path}: {e}"
            )

        return None

    def analyze_product_image(
        self,
        image_path: str
    ) -> Optional[str]:

        api_key = self.gemini_key or os.getenv("GEMINI_API_KEY")

        if not api_key:
            logging.warning("Không tìm thấy GEMINI_API_KEY.")
            return None

        if not os.path.exists(image_path):
            logging.warning(
                f"Không tìm thấy file ảnh: {image_path}"
            )
            return None

        b64_img = self._encode_image(image_path)

        if not b64_img:
            return None

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.1-flash-lite:"
            f"generateContent?key={api_key}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Hãy nhìn kỹ hình ảnh này và cho biết "
                                "đây là sản phẩm gì. "
                                "Nêu tên sản phẩm, kiểu dáng, chất liệu, "
                                "màu sắc và công dụng. "
                                "Trả lời ngắn gọn dưới 40 từ bằng tiếng Việt."
                            )
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64_img
                            }
                        }
                    ]
                }
            ]
        }

        try:
            res = requests.post(
                url,
                json=payload,
                timeout=20
            )

            if res.status_code == 200:
                data = res.json()

                desc = (
                    data["candidates"][0]
                    ["content"]["parts"][0]["text"]
                    .strip()
                )

                logging.info(
                    f"Vision AI đã quét ảnh: {desc}"
                )

                return desc

            logging.warning(
                f"Gemini Vision lỗi {res.status_code}: {res.text}"
            )

        except Exception as e:
            logging.warning(
                f"Phân tích Vision AI lỗi: {e}"
            )

        return None

    # =========================================================
    # CEREBRAS
    # =========================================================

    def _call_cerebras(
        self,
        prompt: str
    ) -> Optional[str]:

        api_key = (
            self.cerebras_key
            or os.getenv("CEREBRAS_API_KEY")
        )

        if not api_key:
            return None

        url = "https://api.cerebras.ai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama3.1-70b",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }

        try:
            res = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if res.status_code == 200:
                return (
                    res.json()["choices"][0]
                    ["message"]["content"]
                )

            logging.warning(
                f"Cerebras lỗi {res.status_code}: {res.text}"
            )

        except Exception as e:
            logging.warning(
                f"Cerebras Exception: {e}"
            )

        return None

    # =========================================================
    # AIML API
    # =========================================================

    def _call_aimlapi(
        self,
        prompt: str
    ) -> Optional[str]:

        api_key = (
            self.aiml_key
            or os.getenv("AIMLAPI_KEY")
        )

        if not api_key:
            return None

        url = "https://api.aimlapi.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }

        try:
            res = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if res.status_code == 200:
                return (
                    res.json()["choices"][0]
                    ["message"]["content"]
                )

            logging.warning(
                f"AIMLAPI lỗi {res.status_code}: {res.text}"
            )

        except Exception as e:
            logging.warning(
                f"AIMLAPI Exception: {e}"
            )

        return None

    # =========================================================
    # GROQ
    # =========================================================

    def _call_groq(
        self,
        prompt: str
    ) -> Optional[str]:

        api_key = (
            self.groq_key
            or os.getenv("GROQ_API_KEY")
        )

        if not api_key:
            return None

        url = (
            "https://api.groq.com/openai/v1/"
            "chat/completions"
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }

        try:
            res = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if res.status_code == 200:
                return (
                    res.json()["choices"][0]
                    ["message"]["content"]
                )

            logging.warning(
                f"Groq lỗi {res.status_code}: {res.text}"
            )

        except Exception as e:
            logging.warning(
                f"Groq Exception: {e}"
            )

        return None

    # =========================================================
    # OPENROUTER
    # =========================================================

    def _call_openrouter(
        self,
        prompt: str
    ) -> Optional[str]:

        api_key = (
            self.openrouter_key
            or os.getenv("OPENROUTER_API_KEY")
        )

        if not api_key:
            return None

        url = (
            "https://openrouter.ai/api/v1/"
            "chat/completions"
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000"
        }

        payload = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }

        try:
            res = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if res.status_code == 200:
                return (
                    res.json()["choices"][0]
                    ["message"]["content"]
                )

            logging.warning(
                f"OpenRouter lỗi {res.status_code}: {res.text}"
            )

        except Exception as e:
            logging.warning(
                f"OpenRouter Exception: {e}"
            )

        return None

    # =========================================================
    # GEMINI
    # =========================================================

    def _call_gemini(
        self,
        prompt: str
    ) -> Optional[str]:

        api_key = (
            self.gemini_key
            or os.getenv("GEMINI_API_KEY")
        )

        if not api_key:
            logging.warning(
                "Không tìm thấy GEMINI_API_KEY."
            )
            return None

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.1-flash-lite:"
            f"generateContent?key={api_key}"
        )

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        try:
            res = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if res.status_code == 200:
                data = res.json()

                return (
                    data["candidates"][0]
                    ["content"]["parts"][0]["text"]
                )

            logging.warning(
                f"Gemini lỗi {res.status_code}: {res.text}"
            )

        except Exception as e:
            logging.warning(
                f"Gemini Exception: {e}"
            )

        return None

    # =========================================================
    # OPENAI
    # =========================================================

    def _call_chatgpt(
        self,
        prompt: str
    ) -> Optional[str]:

        api_key = (
            self.openai_key
            or os.getenv("OPENAI_API_KEY")
        )

        if not api_key:
            return None

        url = (
            "https://api.openai.com/v1/"
            "chat/completions"
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Bạn là chuyên gia Marketing "
                        "Affiliate Short Video."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }

        try:
            res = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if res.status_code == 200:
                return (
                    res.json()["choices"][0]
                    ["message"]["content"]
                )

            logging.warning(
                f"ChatGPT lỗi {res.status_code}: {res.text}"
            )

        except Exception as e:
            logging.warning(
                f"ChatGPT Exception: {e}"
            )

        return None

    # =========================================================
    # NVIDIA
    # =========================================================

    def _call_nvidia_nim(
        self,
        prompt: str
    ) -> Optional[str]:

        api_key = (
            self.nvidia_key
            or os.getenv("NVIDIA_API_KEY")
        )

        if not api_key:
            return None

        url = (
            "https://integrate.api.nvidia.com/v1/"
            "chat/completions"
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "meta/llama-3.3-70b-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }

        try:
            res = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if res.status_code == 200:
                return (
                    res.json()["choices"][0]
                    ["message"]["content"]
                )

            logging.warning(
                f"NVIDIA lỗi {res.status_code}: {res.text}"
            )

        except Exception as e:
            logging.warning(
                f"NVIDIA Exception: {e}"
            )

        return None

    # =========================================================
    # JSON CLEANER
    # =========================================================

    def _clean_json_response(
        self,
        raw_response: str
    ) -> Optional[Dict]:

        if not raw_response:
            return None

        cleaned = raw_response.strip()

        # Loại bỏ markdown code block
        if "```json" in cleaned:
            cleaned = (
                cleaned
                .split("```json", 1)[1]
                .split("```", 1)[0]
                .strip()
            )

        elif "```" in cleaned:
            cleaned = (
                cleaned
                .split("```", 1)[1]
                .split("```", 1)[0]
                .strip()
            )

        # Tìm JSON object nếu model thêm text bên ngoài
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1:
            cleaned = cleaned[start:end + 1]

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            logging.warning(
                f"JSON không hợp lệ: {e}"
            )

        return None

    # =========================================================
    # GENERATE SCRIPT
    # =========================================================

    def generate_script(
        self,
        product_info: Dict,
        sample_image_path: Optional[str] = None
    ) -> Optional[VideoScript]:

        raw_price = product_info.get("price", 0)

        try:
            formatted_price = (
                f"{int(raw_price):,} VNĐ"
            )
        except (ValueError, TypeError):
            formatted_price = (
                f"{raw_price} VNĐ"
                if raw_price
                else "Liên hệ"
            )

        title = product_info.get(
            "title",
            "Sản phẩm"
        )

        desc = product_info.get(
            "description",
            ""
        )

        # -----------------------------------------------------
        # PHÂN TÍCH ẢNH
        # -----------------------------------------------------

        image_analysis_prompt = ""

        if (
            sample_image_path
            and os.path.exists(sample_image_path)
        ):
            vision_desc = self.analyze_product_image(
                sample_image_path
            )

            if vision_desc:
                image_analysis_prompt = (
                    f"- Phân tích thực tế từ ảnh upload: "
                    f"{vision_desc}"
                )

        # -----------------------------------------------------
        # PROMPT
        # -----------------------------------------------------

        prompt = f"""
Bạn là một chuyên gia Marketing Affiliate
TikTok/Reels đỉnh cao.

Hãy tạo bộ nội dung bán hàng khớp 100%
với thông tin sản phẩm sau:

- Tên sản phẩm: {title}
- Mô tả và đặc tính sản phẩm: {desc}
{image_analysis_prompt}
- Giá bán: {formatted_price}

YÊU CẦU ĐẦU RA:

Chỉ được trả về MỘT CHUỖI JSON HỢP LỆ.

Không viết bất kỳ câu dẫn nào bên ngoài JSON.

JSON phải có đúng cấu trúc:

{{
  "voiceover": "Lời đọc lồng tiếng ngắn gọn 15-20 giây. Viết bằng văn bản thuần túy 100 phần trăm. Không chứa ký tự đặc biệt. Không ghi chú HOOK. Không ghi chú chuyển cảnh. Tập trung mô tả đúng điểm ăn tiền của sản phẩm và kêu gọi bấm vào giỏ hàng.",
  "caption": "Caption TikTok gây chú ý mạnh bằng Hook hoặc FOMO, kèm 4-5 hashtag phù hợp.",
  "seeding_comments": [
    "Bình luận mồi hỏi giá hoặc ưu đãi",
    "Bình luận mồi hỏi tính năng, chất liệu hoặc bảo hành",
    "Bình luận mồi khen sản phẩm hoặc giao hàng",
    "Bình luận mồi hỏi link mua hàng",
    "Bình luận mồi hỏi chính sách đổi trả"
  ]
}}
"""

        # -----------------------------------------------------
        # PROVIDERS
        # -----------------------------------------------------

        all_providers = [
            (
                "Cerebras (Llama-3.1 70B)",
                self._call_cerebras,
                self.cerebras_key
            ),
            (
                "AIML API (Llama-3.3)",
                self._call_aimlapi,
                self.aiml_key
            ),
            (
                "Groq (Llama-3.3)",
                self._call_groq,
                self.groq_key
            ),
            (
                "OpenRouter (Free Llama)",
                self._call_openrouter,
                self.openrouter_key
            ),
            (
                "Google Gemini",
                self._call_gemini,
                self.gemini_key
            ),
            (
                "ChatGPT (GPT-4o-mini)",
                self._call_chatgpt,
                self.openai_key
            ),
            (
                "NVIDIA NIM (Llama-3.3)",
                self._call_nvidia_nim,
                self.nvidia_key
            )
        ]

        # Chỉ lấy provider có API key
        available = [
            (name, func)
            for name, func, key in all_providers
            if key
        ]

        if not available:
            logging.error(
                "Không tìm thấy bất kỳ API Key nào trong .env!"
            )
            return None

        # -----------------------------------------------------
        # KHÔNG RANDOM
        # Ưu tiên Gemini trước để dễ debug
        # -----------------------------------------------------

        priority_order = [
            "Google Gemini",
            "Groq (Llama-3.3)",
            "OpenRouter (Free Llama)",
            "ChatGPT (GPT-4o-mini)",
            "Cerebras (Llama-3.1 70B)",
            "AIML API (Llama-3.3)",
            "NVIDIA NIM (Llama-3.3)"
        ]

        available_dict = {
            name: func
            for name, func in available
        }

        ordered_providers = []

        for name in priority_order:
            if name in available_dict:
                ordered_providers.append(
                    (name, available_dict[name])
                )

        # -----------------------------------------------------
        # THỬ TỪNG PROVIDER
        # -----------------------------------------------------

        for name, func in ordered_providers:

            logging.info(
                f"[Auto-Pick] Đang thử AI Model: {name}"
            )

            try:
                raw_response = func(prompt)

            except Exception as e:
                logging.warning(
                    f"{name} Exception: {e}"
                )
                continue

            if not raw_response:
                logging.warning(
                    f"{name} không trả về kết quả. "
                    f"Chuyển model tiếp theo..."
                )
                continue

            # -------------------------------------------------
            # PARSE JSON
            # -------------------------------------------------

            data = self._clean_json_response(
                raw_response
            )

            if not data:
                logging.warning(
                    f"{name} trả về JSON không hợp lệ. "
                    f"Chuyển model tiếp theo..."
                )
                continue

            voiceover = data.get(
                "voiceover",
                ""
            )

            caption = data.get(
                "caption",
                ""
            )

            seeding_comments = data.get(
                "seeding_comments",
                []
            )

            if not isinstance(
                seeding_comments,
                list
            ):
                seeding_comments = []

            logging.info(
                f"Tạo kịch bản thành công bằng model: "
                f"{name}"
            )

            return VideoScript(
                product_title=title,
                voiceover=voiceover,
                caption=caption,
                seeding_comments=seeding_comments,
                used_model=name
            )

        logging.error(
            "Tất cả Provider đều không tạo được "
            "kịch bản thành công!"
        )

        return None