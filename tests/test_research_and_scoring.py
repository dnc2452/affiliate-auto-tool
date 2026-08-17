import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from PIL import Image
from agents.content_agent import ContentAgent
from agents.research_agent import ResearchAgent
from agents.video_agent import VideoAgent
from core.database import Database
from modules.analytics_service import build_summary, parse_analytics_csv
from modules.package_manager import ReadyToPostManager
from modules.product_finder import ProductAnalyzer, ProductMetrics
from modules.product_importer import import_products_csv
from modules.script_generator import VideoScript


class FakeScraper:
    def search(self, keyword, platform, limit):
        return [{
            "product_id": "real-1", "title": "Đèn cảm biến thông minh", "price": 159000,
            "sales_count": 2400, "rating": 4.8, "review_count": 850,
            "commission_rate": 12, "is_official_shop": True,
            "product_url": "https://example.com/p/1", "image_url": "https://example.com/p.jpg",
        }]

    def inspect_product_url(self, product_url, platform):
        return {
            "product_id": product_url, "title": "Đèn từ link trực tiếp", "price": 159000,
            "sales_count": 2400, "rating": 4.8, "review_count": 850,
            "commission_rate": 0, "product_url": product_url, "source": "direct_product_url",
        }


class ResearchAndScoringTests(unittest.TestCase):
    def test_missing_commission_reduces_confidence_without_inventing_data(self):
        result = ProductAnalyzer().analyze(ProductMetrics(product_id="1", title="Sản phẩm", price=200000,
            rating=4.9, review_count=100, product_url="https://example.com"))
        self.assertEqual(result["commission_rate"], 0)
        self.assertLess(result["score_confidence"], 100)
        self.assertTrue(any("hoa hồng" in note for note in result["score_caveats"]))

    def test_real_scraper_data_is_scored_and_persisted(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            agent = ResearchAgent(scraper=FakeScraper())
            agent.db = Database(Path(temporary_directory) / "affiliate.db")
            products = agent.run(keyword="đèn", platform="shopee", limit=5, min_score=0)
            self.assertEqual(len(products), 1)
            self.assertEqual(products[0]["source"], "playwright_public")
            self.assertGreater(products[0]["winner_score"], 60)
            self.assertEqual(len(agent.db.get_products()), 1)

    def test_direct_product_url_is_preserved_for_the_content_workflow(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            agent = ResearchAgent(scraper=FakeScraper())
            agent.db = Database(Path(temporary_directory) / "affiliate.db")
            products = agent.run(product_url="https://example.com/p/exact", platform="shopee", min_score=0)
            self.assertEqual(products[0]["product_url"], "https://example.com/p/exact")
            self.assertEqual(products[0]["source"], "direct_product_url")

    def test_upsert_returns_stable_database_id(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Database(Path(temporary_directory) / "affiliate.db")
            item = {"platform": "shopee", "product_id": "same", "title": "Sản phẩm", "price": 1}
            self.assertEqual(database.save_product(item), database.save_product(item))

    def test_affiliate_csv_is_normalized_for_the_same_scoring_pipeline(self):
        products = import_products_csv(
            "Tên sản phẩm,Giá,Đã bán,Đánh giá,Số review,Hoa hồng,Link affiliate\nĐèn,199000,500,4.9,50,12%,https://a.example".encode(),
            "shopee",
        )
        self.assertEqual(products[0]["commission_rate"], 12)
        self.assertEqual(products[0]["sales_count"], 500)

    def test_reviewed_content_is_persisted_for_product_loaded_from_database(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Database(Path(temporary_directory) / "affiliate.db")
            product_id = database.save_product({"platform": "shopee", "product_id": "p-1", "title": "Đèn", "price": 1})
            agent = ContentAgent.__new__(ContentAgent)
            agent.db = database
            agent.generator = Mock()
            agent.generator.generate_script.return_value = VideoScript(
                product_title="Đèn", voiceover="Bật sáng ngay. Dễ dùng.", caption="Đèn tốt",
                seeding_comments=["Dễ lắp"], used_model="test",
            )
            agent.log_info = Mock()
            agent.log_error = Mock()
            result = agent.run({"id": product_id, "title": "Đèn", "price": 1}, language="en")
            self.assertIsInstance(result["content_id"], int)
            self.assertEqual(result["hook"], "Bật sáng ngay")
            self.assertEqual(result["language"], "en")
            self.assertEqual(agent.generator.generate_script.call_args.kwargs["language"], "en")

    def test_package_contains_reviewed_copy_media_and_thumbnail(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            image = root / "source.png"
            Image.new("RGB", (20, 20), "red").save(image)
            audio = root / "voice.mp3"
            audio.write_bytes(b"audio")
            video = root / "video.mp4"
            video.write_bytes(b"video")
            result = ReadyToPostManager(root).create(
                {"title": "Đèn", "product_url": "https://example.test/p"},
                {"voiceover": "Voice", "caption": "Caption", "hook": "Hook", "hashtags": "#den", "seeding_comments": ["Comment"]},
                {"audio_path": str(audio), "video_path": str(video), "thumbnail_path": str(image)},
            )
            package = Path(result["package_path"])
            self.assertTrue((package / "voiceover.txt").exists())
            self.assertTrue((package / "video.mp4").exists())
            self.assertTrue((package / "thumbnail.jpg").exists())

    def test_analytics_import_normalizes_and_summarizes(self):
        records = parse_analytics_csv(
            "Ngày,Tên sản phẩm,Lượt nhấp,Đơn hàng,Doanh thu,Hoa hồng\n2026-08-18,Đèn,100,4,500000,50000".encode(),
            "shopee",
        )
        summary = build_summary(records)
        self.assertEqual(summary["totals"]["orders"], 4)
        self.assertEqual(summary["totals"]["conversion_rate"], 4)


if __name__ == "__main__":
    unittest.main()
