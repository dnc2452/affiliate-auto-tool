import os
import base64
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class CosmosVideoGenerator:
    """
    Module tích hợp NVIDIA Cosmos API để khởi tạo video AI 
    dựa trên Lời nhắc (Prompt) hoặc Ảnh sản phẩm.
    """
    def __init__(self, output_dir: str = "output/videos"):
        self.output_dir = output_dir
        self.api_key = os.getenv("NVIDIA_API_KEY")
        # ĐÃ CẬP NHẬT: Endpoint chuẩn chính thức của NVIDIA Integrate dành cho Cosmos Diffusion
        self.api_url = "https://integrate.api.nvidia.com/v1/genai/nvidia/cosmos-1-0-diffusion-7b-text2world"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_video(self, prompt: str, output_filename: str = "cosmos_generated.mp4") -> str:
        """
        Gửi request đến NVIDIA API và giải mã b64_video thành file MP4.
        """
        if not self.api_key:
            logging.error("LỖI: Chưa cấu hình NVIDIA_API_KEY trong file .env!")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Payload theo cấu trúc chuẩn API NVIDIA Cosmos
        payload = {
            "prompt": prompt,
            "resolution": "720x1280",  # Khung hình chuẩn TikTok/Reels/Shorts (9:16)
            "num_output_frames": 189,   # Số khung hình đầu ra mặc định (~7-8s video)
            "seed": 42
        }

        logging.info("Đang gửi request sinh video đến NVIDIA Cosmos API...")
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=180)
            
            if response.status_code == 200:
                data = response.json()
                b64_video = data.get("b64_video") or data.get("video")
                
                if b64_video:
                    output_path = os.path.join(self.output_dir, output_filename)
                    video_data = base64.b64decode(b64_video)
                    
                    with open(output_path, "wb") as f:
                        f.write(video_data)
                    
                    logging.info(f"✅ Đã tạo thành công video MP4 từ Cosmos: {output_path}")
                    return output_path
                else:
                    logging.error("LỖI: API NVIDIA trả về kết quả 200 nhưng không tìm thấy trường 'b64_video'.")
                    return None
            else:
                logging.error(f"LỖI API NVIDIA ({response.status_code}): {response.text}")
                return None

        except requests.exceptions.Timeout:
            logging.error("LỖI: Thời gian chờ (timeout) API NVIDIA quá hạn.")
            return None
        except Exception as e:
            logging.error(f"LỖI phát sinh khi gọi Cosmos API: {e}")
            return None