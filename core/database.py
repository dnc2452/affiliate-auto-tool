"""SQLite persistence with additive, safe schema migrations."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import DATABASE_PATH


class Database:
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT, platform TEXT NOT NULL,
                product_id TEXT, title TEXT NOT NULL, price REAL,
                commission_rate REAL, sales_count INTEGER, rating REAL,
                product_url TEXT, winner_score REAL, status TEXT DEFAULT 'new',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform, product_id))""")
            self._add_missing_columns(conn, "products", {
                "review_count": "INTEGER DEFAULT 0", "shop_name": "TEXT DEFAULT ''",
                "image_url": "TEXT DEFAULT ''", "affiliate_url": "TEXT DEFAULT ''",
                "description": "TEXT DEFAULT ''", "source": "TEXT DEFAULT ''",
                "score_breakdown": "TEXT DEFAULT '{}'", "score_confidence": "REAL DEFAULT 0",
                "research_notes": "TEXT DEFAULT ''", "discovered_at": "TEXT",
            })
            conn.execute("""CREATE TABLE IF NOT EXISTS contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, voiceover TEXT,
                caption TEXT, seeding_comments TEXT, model_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id))""")
            conn.execute("""CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, content_id INTEGER, video_path TEXT,
                audio_path TEXT, status TEXT DEFAULT 'created', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES contents(id))""")
            conn.execute("""CREATE TABLE IF NOT EXISTS research_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT NOT NULL, platform TEXT NOT NULL,
                source TEXT NOT NULL, requested_limit INTEGER, result_count INTEGER DEFAULT 0,
                error_message TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS ready_to_post_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
                package_path TEXT NOT NULL, manifest_path TEXT NOT NULL, status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id))""")
            conn.execute("""CREATE TABLE IF NOT EXISTS analytics_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT, platform TEXT NOT NULL, record_date TEXT,
                product_name TEXT DEFAULT '', product_external_id TEXT DEFAULT '', content_name TEXT DEFAULT '',
                channel TEXT DEFAULT '', clicks INTEGER DEFAULT 0, orders INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0, commission REAL DEFAULT 0, spend REAL DEFAULT 0,
                source_file TEXT DEFAULT '', imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
                record_hash TEXT NOT NULL UNIQUE)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS assistant_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL, message TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

    @staticmethod
    def _add_missing_columns(conn: sqlite3.Connection, table: str, columns: Dict[str, str]) -> None:
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    def record_research_run(self, keyword: str, platform: str, source: str, requested_limit: int,
                            result_count: int = 0, error_message: str = "") -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("""INSERT INTO research_runs
                (keyword, platform, source, requested_limit, result_count, error_message)
                VALUES (?, ?, ?, ?, ?, ?)""", (keyword, platform, source, requested_limit, result_count, error_message))
            return int(cursor.lastrowid)

    def save_product(self, product: Dict[str, Any]) -> int:
        platform = product.get("platform", "unknown")
        product_id = str(product.get("product_id") or product.get("product_url") or product.get("title"))
        now = datetime.now().isoformat()
        values = (platform, product_id, product.get("title"), product.get("price", 0),
                  product.get("commission_rate", 0), product.get("sales_count") or product.get("sales_count_30d", 0),
                  product.get("rating", 0), product.get("review_count", 0), product.get("product_url", ""),
                  product.get("affiliate_url", ""), product.get("shop_name", ""), product.get("image_url", ""),
                  product.get("description", ""), product.get("source", ""), product.get("winner_score", 0),
                  json.dumps(product.get("score_breakdown", {}), ensure_ascii=False), product.get("score_confidence", 0),
                  "\n".join(product.get("score_caveats", [])), product.get("status", "new"), now, now)
        with self._get_connection() as conn:
            conn.execute("""INSERT INTO products (
                platform, product_id, title, price, commission_rate, sales_count, rating, review_count,
                product_url, affiliate_url, shop_name, image_url, description, source, winner_score,
                score_breakdown, score_confidence, research_notes, status, discovered_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(platform, product_id) DO UPDATE SET
                title=excluded.title, price=excluded.price, commission_rate=excluded.commission_rate,
                sales_count=excluded.sales_count, rating=excluded.rating, review_count=excluded.review_count,
                product_url=excluded.product_url, affiliate_url=excluded.affiliate_url, shop_name=excluded.shop_name,
                image_url=excluded.image_url, description=excluded.description, source=excluded.source,
                winner_score=excluded.winner_score, score_breakdown=excluded.score_breakdown,
                score_confidence=excluded.score_confidence, research_notes=excluded.research_notes,
                status=excluded.status, updated_at=excluded.updated_at""", values)
            row = conn.execute("SELECT id FROM products WHERE platform = ? AND product_id = ?", (platform, product_id)).fetchone()
            return int(row["id"])

    def get_products(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            query = "SELECT * FROM products"
            params: List[Any] = []
            if status:
                query += " WHERE status = ?"
                params.append(status)
            query += " ORDER BY winner_score DESC, updated_at DESC LIMIT ?"
            params.append(limit)
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def update_product_status(self, product_id: int, status: str) -> None:
        """Move a product through the local production workflow."""
        allowed = {"new", "approved", "in_production", "packaged", "archived"}
        if status not in allowed:
            raise ValueError(f"Trạng thái không hợp lệ: {status}")
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE products SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.now().isoformat(), product_id),
            )

    def save_content(self, product_db_id: int, content: Dict[str, Any]) -> int:
        seeding = content.get("seeding_comments", [])
        if isinstance(seeding, list):
            seeding = "\n".join(seeding)
        with self._get_connection() as conn:
            cursor = conn.execute("""INSERT INTO contents (product_id, voiceover, caption, seeding_comments, model_used)
                VALUES (?, ?, ?, ?, ?)""", (product_db_id, content.get("voiceover"), content.get("caption"),
                                                seeding, content.get("used_model") or content.get("model_used")))
            return int(cursor.lastrowid)

    def update_content(self, content_id: int, content: Dict[str, Any]) -> None:
        """Persist a reviewed content draft without creating duplicate rows."""
        seeding = content.get("seeding_comments", [])
        if isinstance(seeding, list):
            seeding = "\n".join(seeding)
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE contents
                   SET voiceover = ?, caption = ?, seeding_comments = ?, model_used = ?
                   WHERE id = ?""",
                (
                    content.get("voiceover", ""),
                    content.get("caption", ""),
                    seeding,
                    content.get("used_model") or content.get("model_used", ""),
                    content_id,
                ),
            )

    def save_video(self, content_id: int, video_path: str, audio_path: str = "", status: str = "created") -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("""INSERT INTO videos (content_id, video_path, audio_path, status)
                VALUES (?, ?, ?, ?)""", (content_id, video_path, audio_path, status))
            return int(cursor.lastrowid)

    def save_ready_package(self, product_id: int, package_path: str, manifest_path: str, status: str = "draft") -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("""INSERT INTO ready_to_post_packages (product_id, package_path, manifest_path, status)
                VALUES (?, ?, ?, ?)""", (product_id, package_path, manifest_path, status))
            return int(cursor.lastrowid)

    def get_ready_packages(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            return [dict(row) for row in conn.execute(
                """SELECT packages.*, products.title AS product_title
                   FROM ready_to_post_packages AS packages
                   JOIN products ON products.id = packages.product_id
                   ORDER BY packages.id DESC LIMIT ?""",
                (limit,),
            ).fetchall()]

    def import_analytics(self, records: List[Dict[str, Any]], platform: str, source_file: str) -> int:
        inserted = 0
        with self._get_connection() as conn:
            for record in records:
                try:
                    cursor = conn.execute("""INSERT OR IGNORE INTO analytics_records
                        (platform, record_date, product_name, product_external_id, content_name, channel,
                         clicks, orders, revenue, commission, spend, source_file, record_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (platform, record.get("record_date", ""), record.get("product_name", ""),
                         record.get("product_external_id", ""), record.get("content_name", ""), record.get("channel", platform),
                         record.get("clicks", 0), record.get("orders", 0), record.get("revenue", 0),
                         record.get("commission", 0), record.get("spend", 0), source_file, record["record_hash"]))
                    inserted += cursor.rowcount
                except (KeyError, sqlite3.Error):
                    continue
        return inserted

    def get_analytics_records(self, limit: int = 10_000) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM analytics_records ORDER BY record_date DESC, id DESC LIMIT ?", (limit,)
            ).fetchall()]

    def save_assistant_message(self, role: str, message: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("INSERT INTO assistant_messages (role, message) VALUES (?, ?)", (role, message))
            return int(cursor.lastrowid)

    def get_assistant_messages(self, limit: int = 30) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM assistant_messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return list(reversed([dict(row) for row in rows]))
