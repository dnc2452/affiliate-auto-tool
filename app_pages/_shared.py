from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from core.database import Database


@st.cache_resource
def database() -> Database:
    return Database()


def initialize_state() -> None:
    st.session_state.setdefault("selected_product", None)
    st.session_state.setdefault("latest_content", None)
    st.session_state.setdefault("latest_media", None)
    st.session_state.setdefault("research_results", [])


def products_frame(products: List[Dict[str, Any]]) -> pd.DataFrame:
    columns = ["title", "platform", "price", "sales_count", "rating", "review_count", "commission_rate", "winner_score", "score_confidence", "status", "product_url"]
    return pd.DataFrame(products).reindex(columns=columns)


def product_label(product: Dict[str, Any]) -> str:
    return f"{product['title']} · {product.get('winner_score', 0):.1f}/100"


def save_upload(upload: Any, destination: Path, prefix: str) -> str:
    """Save an uploaded file under a safe, collision-resistant local filename."""
    suffix = Path(getattr(upload, "name", "")).suffix.lower()
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(getattr(upload, "name", "upload")).stem).strip("-")
    safe_name = f"{prefix}_{safe_stem[:48] or 'upload'}{suffix}"
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / safe_name
    path.write_bytes(upload.getvalue())
    return str(path)


def parse_comments(value: str) -> List[str]:
    return [line.strip("- ").strip() for line in value.splitlines() if line.strip("- ").strip()]
