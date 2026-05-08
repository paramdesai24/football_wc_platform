"""
Data loading utilities for the pipeline.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def load_csv(file_path: Path, **kwargs) -> Optional[pd.DataFrame]:
    """Load CSV file safely with error handling."""
    try:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        # Use low_memory=False to avoid mixed-type dtype warnings and improve parsing
        read_kwargs = {"low_memory": False}
        read_kwargs.update(kwargs)
        df = pd.read_csv(file_path, **read_kwargs)
        logger.info(f"✓ Loaded {file_path.name}: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        # Fallback for very large or irregular CSVs that can fail with C parser OOM/tokenization.
        message = str(e).lower()
        if "out of memory" in message or "error tokenizing data" in message:
            try:
                logger.warning(
                    f"Primary CSV read failed for {file_path.name}; retrying with python engine"
                )
                fallback_kwargs = {"engine": "python", "on_bad_lines": "skip"}
                fallback_kwargs.update(kwargs)
                df = pd.read_csv(file_path, **fallback_kwargs)
                logger.info(
                    f"✓ Loaded {file_path.name} with fallback parser: {len(df)} rows, {len(df.columns)} columns"
                )
                return df
            except Exception as fallback_error:
                logger.error(f"Fallback load failed for {file_path}: {fallback_error}")
                return None

        logger.error(f"Failed to load {file_path}: {e}")
        return None


def save_csv(df: pd.DataFrame, file_path: Path, index: bool = False) -> bool:
    """Save DataFrame to CSV safely."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(file_path, index=index)
        logger.info(f"✓ Saved {file_path.name}: {len(df)} rows")
        return True
    except Exception as e:
        logger.error(f"Failed to save {file_path}: {e}")
        return False


class DataLoader:
    """Centralized data loader."""
    
    def __init__(self, datasets_config: dict):
        self.config = datasets_config
        self.data = {}
    
    def load_all(self) -> dict:
        """Load all datasets."""
        for name, path in self.config.items():
            self.data[name] = load_csv(path)
        return self.data
    
    def load(self, name: str) -> Optional[pd.DataFrame]:
        """Load a specific dataset."""
        if name not in self.config:
            logger.warning(f"Unknown dataset: {name}")
            return None
        path = self.config[name]
        df = load_csv(path)
        if df is not None:
            self.data[name] = df
        return df
    
    def get(self, name: str) -> Optional[pd.DataFrame]:
        """Get loaded dataset from cache."""
        return self.data.get(name)
