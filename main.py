import os
import logging
from dotenv import load_dotenv

from modules.script_generator import MultiModelScriptGenerator
from modules.voice_generator import VoiceGenerator
from modules.video_creator import VideoCreator
from modules.cosmos_generator import CosmosVideoGenerator
from modules.clipchamp_integration import ClipchampLauncher

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_affiliate_pipeline(product_info: dict, product_images: list, use_cosmos: bool = False):
    logging.info("=== BẮT ĐẦU TỰ ĐỘNG HÓA QUY TRÌNH NỘI DUNG AFFILIATE ===")
    
    # 0. Ép kiểu an toàn hiển thị giá tiền trên log
    raw_price = product_info.get('price', 0)
    try:
        price_str = f"{int(raw_price):,} VNĐ"
    except (ValueError, TypeError):
        price_str = f"{raw_price} VNĐ"
        
    logging.info(f"Sản phẩm xử lý: {product_info.get('title', 'Sản phẩm')} - Giá: {price_str}")

    # Lấy đường dẫn ảnh đầu tiên để Vision AI phân tích (nếu có)
    sample_image = product_images[0] if (product_images and os.path.exists(product_images[0])) else None

    # 1. Tạo bộ nội dung AI (Voiceover, Caption, Seeding) + Vision AI đọc ảnh thực tế
    script_gen = MultiModelScriptGenerator()
    script = script_gen.generate_script(product_info, sample_image_path=sample_image)
    
    if not script:
        logging.error("Lỗi: Không thể khởi tạo kịch bản. Dừng quy trình!")
        return

    logging.info(f"-> Đã tạo kịch bản thành công từ model: [{script.used_model}]")

    # 2. Tạo giọng đọc MP3 từ voiceover
    voice_gen = VoiceGenerator()
    audio_file = voice_gen.text_to_speech(script.voiceover, filename="voiceover_main.mp3")
    
    if not audio_file:
        logging.error("Lỗi: Không thể tạo giọng đọc. Dừng quy trình!")
        return

    # 3. Tạo Video MP4 (Ưu tiên NVIDIA Cosmos -> Fallback về ghép ảnh MoviePy 9:16)
    video_file = None

    if use_cosmos:
        logging.info("Đang thử nghiệm tạo Video AI sinh từ NVIDIA Cosmos API...")
        try:
            cosmos_gen = CosmosVideoGenerator()
            prompt_cosmos = (
                f"A high quality product video showcase of {product_info.get('title')}, "
                "cinematic studio lighting, sharp focus, 4k resolution, dynamic camera movement"
            )
            video_file = cosmos_gen.generate_video(
                prompt=prompt_cosmos,
                output_filename="final_affiliate_cosmos.mp4"
            )
        except Exception as e:
            logging.warning(f"NVIDIA Cosmos không khả dụng: {e}. Chuyển sang dựng ghép ảnh...")

    # Nếu không dùng Cosmos hoặc Cosmos lỗi/chưa cấu hình -> Dùng MoviePy ghép ảnh chuẩn 9:16
    if not video_file:
        logging.info("Tạo video bằng phương pháp ghép ảnh thực tế MoviePy...")
        video_gen = VideoCreator()
        video_file = video_gen.create_video_from_images(
            image_paths=product_images,
            audio_path=audio_file,
            output_filename="final_affiliate_video.mp4"
        )

    if video_file:
        print("\n==================================================")
        print("🎉 QUY TRÌNH HOÀN TẤT THÀNH CÔNG!")
        print(f"📌 Model sử dụng: [{script.used_model}]")
        print("\n🔊 LỜI ĐỌC VOICEOVER (ĐÃ CHUYỂN THÀNH AUDIO):")
        print(f"\"{script.voiceover}\"")
        
        print("\n📝 CAPTION ĐĂNG BÀI (COPY DÁN TIKTOK/REELS):")
        print("--------------------------------------------------")
        print(script.caption)
        print("--------------------------------------------------")
        
        print("\n💬 5 CÂU SEEDING COMMENT MỒI:")
        for idx, cmt in enumerate(script.seeding_comments, 1):
            print(f"  {idx}. {cmt}")
            
        print("\n--------------------------------------------------")
        print(f"🔊 File Audio: {audio_file}")
        print(f"🎬 Video hoàn chỉnh: {video_file}")
        print("==================================================\n")

        # 4. Khởi chạy Clipchamp và mở thư mục chứa tài nguyên
        try:
            launcher = ClipchampLauncher()
            launcher.launch_and_open_assets(video_path=video_file, audio_path=audio_file)
        except Exception as launcher_err:
            logging.warning(f"Không thể mở Clipchamp tự động: {launcher_err}")

if __name__ == "__main__":
    # Dữ liệu sản phẩm thử nghiệm
    product = {
        "title": "Vòng tay bạc 925 đính đá cao cấp",
        "price": 199000
    }
    
    # Danh sách ảnh thực tế sản phẩm
    product_images = [
        "assets/images/product1.jpg",
        "assets/images/product2.jpg",
        "assets/images/product3.jpg"
    ]

    # Chạy pipeline (Đặt use_cosmos=False để ưu tiên dựng video từ ảnh thực tế)
    run_affiliate_pipeline(product, product_images, use_cosmos=False)