from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

from core.database import Database
from core.config import DATA_DIR, OUTPUT_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class BaseAgent(ABC):
    """Lớp cơ sở cho tất cả Agent"""

    def __init__(self, name: str = "BaseAgent"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.db = Database()
        self.data_dir = DATA_DIR
        self.output_dir = OUTPUT_DIR

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Mỗi Agent phải implement hàm run()"""
        pass

    def log_info(self, message: str):
        self.logger.info(f"[{self.name}] {message}")

    def log_error(self, message: str):
        self.logger.error(f"[{self.name}] {message}")

    def log_warning(self, message: str):
        self.logger.warning(f"[{self.name}] {message}")