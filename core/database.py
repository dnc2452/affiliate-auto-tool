import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from core.config import DATABASE_PATH


class Database:
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Tạo các bảng cần thiết nếu chưa có"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Bảng sản phẩm đã tìm / đã xử lý
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    product_id TEXT,
                    title TEXT NOT NULL,
                    price REAL,
                    commission_rate REAL,
                    sales_count INTEGER,
                    rating REAL,
                    product_url TEXT,
                    winner_score REAL,
                    status TEXT DEFAULT 'new',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, product_id)
                )
            """)

            # Bảng kịch bản / content đã tạo
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    voiceover TEXT,
                    caption TEXT,
                    seeding_comments TEXT,
                    model_used TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)

            # Bảng video đã render
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id INTEGER,
                    video_path TEXT,
                    audio_path TEXT,
                    status TEXT DEFAULT 'created',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (content_id) REFERENCES contents (id)
                )
            """)

            conn.commit()

    def save_product(self, product: Dict[str, Any]) -> int:
        """Lưu hoặc cập nhật sản phẩm, trả về id"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (
                    platform, product_id, title, price, commission_rate,
                    sales_count, rating, product_url, winner_score, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(platform, product_id) DO UPDATE SET
                    title=excluded.title,
                    price=excluded.price,
                    commission_rate=excluded.commission_rate,
                    sales_count=excluded.sales_count,
                    rating=excluded.rating,
                    product_url=excluded.product_url,
                    winner_score=excluded.winner_score,
                    status=excluded.status,
                    updated_at=excluded.updated_at
            """, (
                product.get("platform", "unknown"),
                product.get("product_id"),
                product.get("title"),
                product.get("price"),
                product.get("commission_rate"),
                product.get("sales_count"),
                product.get("rating"),
                product.get("product_url"),
                product.get("winner_score"),
                product.get("status", "new"),
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def get_products(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM products WHERE status = ? ORDER BY winner_score DESC LIMIT ?",
                    (status, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM products ORDER BY winner_score DESC LIMIT ?",
                    (limit,)
                )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def save_content(self, product_db_id: int, content: Dict[str, Any]) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            seeding = content.get("seeding_comments", [])
            if isinstance(seeding, list):
                seeding = "\n".join(seeding)

            cursor.execute("""
                INSERT INTO contents (product_id, voiceover, caption, seeding_comments, model_used)
                VALUES (?, ?, ?, ?, ?)
            """, (
                product_db_id,
                content.get("voiceover"),
                content.get("caption"),
                seeding,
                content.get("used_model") or content.get("model_used")
            ))
            conn.commit()
            return cursor.lastrowid